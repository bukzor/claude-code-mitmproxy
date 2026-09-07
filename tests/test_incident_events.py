"""A fresh incident is an event: `incidents` records it under
`events.incident.<type>` so the watch can wake on the queue changing, instead
of warning into a stream nothing captures.

The type is derived from the rule: the strip-rate floor is its own kind of
miss, an uncaught exception is not a miss at all, and everything else is a
patch that failed to apply. Only a *fresh* record emits, because the event is
"this was learned once" -- the store's idempotence is what keeps a live proxy
re-hitting one failure from announcing it on every request.
"""

from __future__ import annotations

import logging

import pytest

from claude_mitmproxy import incidents
from claude_mitmproxy import logging_handlers

from test_logging_handlers import messages


@pytest.fixture
def events_root(tmp_path):
    logging_handlers.reinstall_log_handlers(tmp_path / "events", tmp_path / "incidents")
    yield tmp_path / "events"
    logging_handlers.uninstall_log_handlers()


def test_a_fresh_patch_miss_is_a_patch_miss_event(tmp_path, events_root):
    store = tmp_path / "incidents"
    incidents.report_issues("a body", [incidents.Incident("some-patch", "failed to match")], store)
    (line,) = messages(events_root, "incident/patch-miss")
    assert line.startswith("patch 'some-patch' failed to match -> "), line
    assert line.endswith(".json"), line


def test_the_strip_floor_has_its_own_type(tmp_path, events_root):
    store = tmp_path / "incidents"
    issue = incidents.Incident(incidents.STRIP_RULE, "stripped 0.1 below floor 0.3")
    incidents.report_issues("a body", [issue], store)
    assert len(messages(events_root, "incident/strip-floor")) == 1
    assert not list((events_root / "incident").glob("patch-miss*"))


def test_an_uncaught_exception_is_an_uncaught_event(tmp_path, events_root):
    store = tmp_path / "incidents"
    incidents.capture_uncaught("_uncaught-thinkpatch", ValueError("boom"), store)
    (line,) = messages(events_root, "incident/uncaught")
    assert line.startswith("_uncaught-thinkpatch: uncaught ValueError -> "), line


def test_a_repeat_sighting_emits_nothing(tmp_path, events_root):
    store = tmp_path / "incidents"
    issue = incidents.Incident("some-patch", "failed to match")
    incidents.report_issues("a body", [issue], store)
    incidents.report_issues("a body", [issue], store)
    assert len(messages(events_root, "incident/patch-miss")) == 1


def test_an_offline_report_is_a_warning_and_not_an_event(events_root, caplog):
    """`capture_dir=None` is the offline checks: nothing is learned once, so
    nothing is an event; the warning is the whole report."""
    with caplog.at_level(logging.WARNING):
        incidents.report_issues("a body", [incidents.Incident("some-patch", "failed to match")], None)
    assert "patch 'some-patch' failed to match" in caplog.text
    assert not (events_root / "incident").exists()


def test_a_blocked_incident_shard_reports_once_and_stops(tmp_path, events_root):
    """The loop the handler's guard exists for, closed for real.

    A blocked event write files an uncaught incident, which is itself an
    event; block that shard too and the report would arrive back at the
    same failure. One incident on disk and a returning call are the proof.
    """
    from test_flocked_logs import flock_in_subprocess
    from test_logging_handlers import shard

    blocked = [shard(events_root, "lifecycle/reload"), shard(events_root, "incident/uncaught")]
    children = []
    for path in blocked:
        path.parent.mkdir(parents=True, exist_ok=True)
        children.append(flock_in_subprocess(path))
    try:
        logging_handlers.events.lifecycle.reload.info("reloaded")
    finally:
        for child in children:
            child.kill()
            child.wait()
    filed = sorted((tmp_path / "incidents").glob("*/*.json"))
    assert [path.parent.name for path in filed] == [logging_handlers.UNCAUGHT_RULE]
