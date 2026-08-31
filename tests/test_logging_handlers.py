"""Event records land in one file per logger name, and reinstalling is safe.

The taxonomy under `claude_mitmproxy.events` is the published interface: a
consumer tails exactly one path and parses nothing. Reinstalling is what both
reload paths do, so doing it twice must neither duplicate a handler nor lose
the fd the first install locked.
"""

from __future__ import annotations

import logging
from datetime import date

import pytest

from claude_mitmproxy import logging_handlers


@pytest.fixture
def events_root(tmp_path):
    """An events tree under tmp_path, torn down so tests cannot leak handlers."""
    logging_handlers.reinstall_log_handlers(tmp_path)
    yield tmp_path
    logging_handlers.uninstall_log_handlers()


def logged_lines(root, relative):
    path = root / f"{relative}.{date.today():%Y-%m-%d}.log"
    return path.read_text().splitlines()


def messages(root, relative):
    """The lines with their leading timestamp field stripped."""
    return [line.split(" ", 1)[1] for line in logged_lines(root, relative)]


def test_event_lands_in_the_file_its_logger_name_names(events_root):
    logging.getLogger("claude_mitmproxy.events.capture.system-prompt").info(
        "captured new system prompt -> %s", "v2.1.251_abc.raw.md"
    )
    assert messages(events_root, "capture/system-prompt") == [
        "captured new system prompt -> v2.1.251_abc.raw.md"
    ]


def test_line_starts_with_an_iso_date(events_root):
    logging.getLogger("claude_mitmproxy.events.capture.system-prompt").info("captured")
    line = logged_lines(events_root, "capture/system-prompt")[0]
    assert line.startswith(f"{date.today():%Y-%m-%d}"), line


def test_sibling_event_types_get_their_own_files(events_root):
    logging.getLogger("claude_mitmproxy.events.capture.system-prompt").info("main")
    logging.getLogger("claude_mitmproxy.events.capture.subagent-prompt").info("sub")
    assert messages(events_root, "capture/system-prompt") == ["main"]
    assert messages(events_root, "capture/subagent-prompt") == ["sub"]


def test_reinstalling_does_not_duplicate_the_handler(events_root):
    logging_handlers.reinstall_log_handlers(events_root)
    logging_handlers.reinstall_log_handlers(events_root)
    events = logging.getLogger(logging_handlers.EVENTS_LOGGER)
    assert len(events.handlers) == 1, events.handlers


def test_reinstalling_does_not_lose_the_lock_or_drop_events(events_root):
    logging.getLogger("claude_mitmproxy.events.lifecycle.startup").info("before")
    logging_handlers.reinstall_log_handlers(events_root)
    logging.getLogger("claude_mitmproxy.events.lifecycle.startup").info("after")
    assert messages(events_root, "lifecycle/startup") == ["before", "after"]


def test_events_still_propagate_to_the_console(events_root):
    """An operator watching interactively must still see the line.

    Not via caplog: pytest's logging plugin captures records by a route that
    survives `propagate = False`, so a caplog assertion here passes against a
    handler that has stopped reaching the root entirely. A handler of our own
    on the root logger is what the design commitment actually means
    (CLAUDE.kb/console-output-bands.md).
    """
    seen: list[str] = []
    spy = logging.Handler()
    spy.emit = lambda record: seen.append(record.getMessage())
    root = logging.getLogger()
    root.addHandler(spy)
    try:
        logging.getLogger("claude_mitmproxy.events.lifecycle.reload").info("reloaded")
    finally:
        root.removeHandler(spy)
    assert seen == ["reloaded"], seen
