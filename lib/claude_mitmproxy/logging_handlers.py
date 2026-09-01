"""One place deciding where this repo's addon output lands.

Every addon logs through `logging` and mitmdump sends the lot to stderr, which
`proxy.sh` never captures -- so the proxy announces a fact it knows exactly
once and then discards the announcement. Records under the `events` tree below
are the subset a consumer wants as *news*: deduplicated, one line each, in a
tailable file per event type rather than as prose in a mixed stream.

The logger name is the interface: `events.capture.system_prompt` writes
`log/events/capture/system-prompt.<date>.log`, so a consumer subscribes by
tailing a path and parses nothing.

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
from claude_mitmproxy import incidents
from claude_mitmproxy import repo_paths

PACKAGE_LOGGER = "claude_mitmproxy"
HANDLER_NAME = "claude-mitmproxy-events"
# Named like every addon's: a write we could not do is an uncaught exception in
# the same sense, and belongs in the same store an operator already triages.
UNCAUGHT_RULE = "_uncaught-events-log"


def path_segment(attribute: str) -> str:
    """`system_prompt` names `system-prompt`. An identifier at the call site, a
    path segment on disk, and the underscore is the whole difference."""
    return attribute.replace("_", "-")


def loggers_named_by_nesting[T: type](tree: T) -> T:
    """Bind each annotated name in a nest of classes to the logger it spells.

    `events.capture.system_prompt` is the logger
    `claude_mitmproxy.events.capture.system-prompt`, which writes
    `log/events/capture/system-prompt.<date>.log`. The nesting is the only
    place that name exists: a table of strings beside the classes would let the
    two drift, and a rename would leave the published name behind.
    """

    def bind(node: type, dotted: str) -> None:
        for attribute in list(node.__dict__.get("__annotations__", ())):
            logger = logging.getLogger(f"{dotted}.{path_segment(attribute)}")
            setattr(node, attribute, logger)
        for attribute, value in list(node.__dict__.items()):
            if isinstance(value, type):
                bind(value, f"{dotted}.{path_segment(attribute)}")

    bind(tree, f"{PACKAGE_LOGGER}.{path_segment(tree.__name__)}")
    return tree


@loggers_named_by_nesting
class events:
    """The ratified taxonomy, and the published interface: a consumer derives a
    `tail -F` path from one of these names, so renaming one is a breaking
    change and should read like one in the diff.

    Emitters hold the logger, never its name -- a `str` says nothing about what
    it is for, and every call site that spelled one was a place the taxonomy
    could be misspelled. Domains are message *categories*, never the module
    that emitted them: a category is what a future handler, filter or level
    might differentiate, while an emitter is an implementation detail a
    refactor renames out from under anyone watching.
    """

    class capture:
        system_prompt: logging.Logger
        subagent_prompt: logging.Logger

    class incident:
        patch_miss: logging.Logger
        strip_floor: logging.Logger
        uncaught: logging.Logger

    class lifecycle:
        startup: logging.Logger
        reload: logging.Logger

    class housekeeping:
        gc: logging.Logger
        compress: logging.Logger


EVENTS_LOGGER = f"{PACKAGE_LOGGER}.{events.__name__}"
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
    open-files-are-rediscovered-not-remembered.md). At a few events a day, the
    scan is free.
    """

    def __init__(self, root: Path, capture_dir: Path | None):
        super().__init__()
        self.root = root
        self.capture_dir = capture_dir
        self.formatter = LINE_FORMAT
        self.reporting = False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            base = log_base(self.root, record.name)
            fd = flocked_logs.reopen_log_file(base, when=date.today())
            os.write(fd, f"{self.format(record)}\n".encode())
        except Exception as exc:
            self.report_failure(record, exc)

    def report_failure(self, record: logging.LogRecord, exc: Exception) -> None:
        """File the failed write as an incident.

        Not stderr: an unwatched stream is the thing this module exists to stop
        relying on, so reporting the *event system's* own failure there is the
        one place it can least afford to. An incident record is durable,
        content-addressed (so a proxy failing on every request records and
        warns once), and lands in the queue an operator already triages.

        Not a re-raise either, though contention is an error rather than
        something to fail soft over: a handler that raises takes down its
        caller -- an addon hook mid-request -- over a *logging* failure, which
        is why `logging` gives handlers `handleError` instead. The error is
        raised where it can be acted on rather than where it happened; the file
        goes quiet, and the incident says so.

        `incidents` warns through `logging`, so if it ever emits an
        `events.incident.*` record, that record arrives right back here, fails
        the same way, and reports forever -- hence the guard. Its import of
        this module would have to be function-local, too; the cycle is why.
        """
        if self.reporting:
            return
        self.reporting = True
        try:
            incidents.capture_uncaught(UNCAUGHT_RULE, exc, self.capture_dir)
        except Exception:
            self.handleError(record)
        finally:
            self.reporting = False


def uninstall_log_handlers() -> None:
    """Remove and close ours, if installed. Idempotent."""
    stale = logging.getHandlerByName(HANDLER_NAME)
    logging.getLogger(EVENTS_LOGGER).handlers = []
    if stale is not None:
        stale.close()


def reinstall_log_handlers(
    root: Path = EVENTS_DIR, capture_dir: Path | None = incidents.CAPTURE_DIR
) -> None:
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
    handler = EventFileHandler(root, capture_dir)
    # After the lookup above: naming a handler overwrites the registry entry,
    # which would otherwise hide the one we are replacing.
    handler.name = HANDLER_NAME
    events = logging.getLogger(EVENTS_LOGGER)
    events.handlers = [handler]
    # Set here rather than inherited: an event is a durable record, so whether
    # it is written must not depend on how loud the console happens to be.
    # mitmproxy sets root to DEBUG, a bare CLI leaves it at WARNING, and the
    # file has to say the same thing under both. DEBUG rather than INFO because
    # this level should gate nothing -- the file takes every event, and how
    # loud to be stays the console handler's business (mitmproxy's
    # TermLogHandler filters at `termlog_verbosity`, INFO by default). That is
    # what leaves a debug-grade event possible: the rotator's "skipped an
    # in-use log" note is recorded without being printed.
    events.setLevel(logging.DEBUG)
    if stale is not None:
        stale.close()
