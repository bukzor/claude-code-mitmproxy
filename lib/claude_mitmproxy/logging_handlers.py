"""One place deciding where this repo's addon output lands.

Every addon logs through `logging` and mitmdump sends the lot to stderr, which
`proxy.sh` never captures -- so the proxy announces a fact it knows exactly
once and then discards the announcement. Records under `EVENTS_LOGGER` are the
subset a consumer wants as *news*: deduplicated, one line each, in a tailable
file per event type rather than as prose in a mixed stream.

The logger name is the interface. `claude_mitmproxy.events.capture.system-prompt`
writes `log/events/capture/system-prompt.<date>.log`, so a consumer subscribes
by tailing a path and parses nothing. Segments name message *categories*, never
the module that emitted them: a category is what a future handler, filter or
level might differentiate, while an emitter is an implementation detail that a
refactor would rename out from under anyone watching.

Records still propagate to the root logger, so mitmproxy's own TermLogHandler
prints them for an operator watching interactively (CLAUDE.kb/
console-output-bands.md). Nothing here silences anything.
"""

from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path

from claude_mitmproxy import flocked_logs
from claude_mitmproxy import repo_paths

EVENTS_LOGGER = "claude_mitmproxy.events"
HANDLER_NAME = "claude-mitmproxy-events"

# The ratified taxonomy. Named here rather than spelled at each emit site
# because these strings are the published interface: a consumer's `tail -F`
# path is derived from one, so renaming a domain is a breaking change and
# should read like one in the diff.
CAPTURE_SYSTEM_PROMPT = f"{EVENTS_LOGGER}.capture.system-prompt"
CAPTURE_SUBAGENT_PROMPT = f"{EVENTS_LOGGER}.capture.subagent-prompt"
INCIDENT_PATCH_MISS = f"{EVENTS_LOGGER}.incident.patch-miss"
INCIDENT_STRIP_FLOOR = f"{EVENTS_LOGGER}.incident.strip-floor"
INCIDENT_UNCAUGHT = f"{EVENTS_LOGGER}.incident.uncaught"
LIFECYCLE_STARTUP = f"{EVENTS_LOGGER}.lifecycle.startup"
LIFECYCLE_RELOAD = f"{EVENTS_LOGGER}.lifecycle.reload"
HOUSEKEEPING_GC = f"{EVENTS_LOGGER}.housekeeping.gc"
HOUSEKEEPING_COMPRESS = f"{EVENTS_LOGGER}.housekeeping.compress"
EVENTS_DIR = repo_paths.LOG / "events"
# Date first so `grep '^2026-08-31'` spans the whole tree with one pattern; the
# path's date only partitions shards, and a reader should not need to know
# where in the path it sits.
LINE_FORMAT = logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z")


def log_base(root: Path, logger_name: str) -> Path:
    """Where records from `logger_name` are sharded, minus the date and suffix.

    The taxonomy below EVENTS_LOGGER becomes directories, with the event type
    as the filename -- so a category is a directory a consumer can watch whole.
    """
    suffix = logger_name.removeprefix(f"{EVENTS_LOGGER}.")
    assert suffix != logger_name, (logger_name, EVENTS_LOGGER)
    return root.joinpath(*suffix.split("."))


class EventFileHandler(logging.Handler):
    """Appends each record to the file its logger name names.

    Holds no path or fd of its own: `reopen_log_file` recomputes the shard per
    record and finds any fd we already hold by scanning, which is what makes
    the day roll over with no rotation branch and makes re-executing this
    module harmless (design/040-design.kb/ease-of-operation.kb/
    reload-rediscovers-open-fds.md). At a few events a day the scan is free.
    """

    def __init__(self, root: Path):
        super().__init__()
        self.root = root
        self.formatter = LINE_FORMAT

    def emit(self, record: logging.LogRecord) -> None:
        base = log_base(self.root, record.name)
        fd = flocked_logs.reopen_log_file(base, when=date.today())
        os.write(fd, f"{self.format(record)}\n".encode())


def uninstall_log_handlers() -> None:
    """Remove and close ours, if installed. Idempotent."""
    stale = logging.getHandlerByName(HANDLER_NAME)
    logging.getLogger(EVENTS_LOGGER).handlers = []
    if stale is not None:
        stale.close()


def reinstall_log_handlers(root: Path = EVENTS_DIR) -> None:
    """Install the events handler, replacing any earlier one. Idempotent.

    Both reload paths re-run this in a process that may already have installed
    a handler, and neither offers a teardown hook, so tearing down is this
    function's own first act. The stale handler is found by *name* because
    `isinstance` cannot see it: re-execution binds a new class object, so the
    live instance is not an instance of the class this module just defined.

    Assigning `handlers` rather than mutating it makes the swap a single store,
    so a concurrent `callHandlers` walk finishes over the list it started on.
    """
    stale = logging.getHandlerByName(HANDLER_NAME)
    handler = EventFileHandler(root)
    # After the lookup above: naming a handler overwrites the registry entry,
    # which would otherwise hide the one we are replacing.
    handler.name = HANDLER_NAME
    events = logging.getLogger(EVENTS_LOGGER)
    events.handlers = [handler]
    # Set here rather than inherited: an event is a durable record, so whether
    # it is written must not depend on how loud the console happens to be.
    # mitmproxy sets root to DEBUG, a bare CLI leaves it at WARNING, and the
    # file has to say the same thing under both.
    events.setLevel(logging.INFO)
    if stale is not None:
        stale.close()
