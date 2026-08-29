"""gc expires live `_uncaught-*` incidents, not just archived ones.

An uncaught-exception incident is the one class with a cause that is
routinely already gone: a live edit the proxy re-executed mid-refactor. Those
cannot be distinguished from a standing bug at capture time, only by waiting
-- so waiting is what expiry does, and a human never has to look.

The safety property is `save_incident`'s idempotence: expiry removes the
record, so a cause that is still live re-files and re-warns on the next
request, while a transient never returns.
"""

from __future__ import annotations

import json
import os
import time

from claude_mitmproxy import gc_patch_failures
from claude_mitmproxy import incidents


def file_incident(capture_dir, rule, body, at_days_ago=0.0):
    digest = incidents.masked_hash(body)
    incidents.save_body(body, digest, capture_dir)
    path = incidents.save_incident(incidents.Incident(rule, "SomeError"), digest, capture_dir)
    if path is not None and at_days_ago:
        old = time.time() - at_days_ago * 86400
        os.utime(path, (old, old))
    return digest, path


def live_incidents(capture_dir):
    return {
        f"{path.parent.name}/{path.stem}"
        for path in capture_dir.glob("*/*.json")
        if path.parent.name != incidents.ARCHIVE_DIRNAME
    }


def test_stale_uncaught_incident_is_expired(tmp_path):
    file_incident(tmp_path, "_uncaught-syspatch", "a stale traceback", at_days_ago=40)
    gc_patch_failures.expire_transients(tmp_path, retention_days=30, dry_run=False)
    assert live_incidents(tmp_path) == set()


def test_fresh_uncaught_incident_is_kept(tmp_path):
    """Freshness is the only evidence that a cause may still be live, so the
    window has to pass before the record can be assumed spent."""
    file_incident(tmp_path, "_uncaught-syspatch", "a fresh traceback")
    gc_patch_failures.expire_transients(tmp_path, retention_days=30, dry_run=False)
    assert live_incidents(tmp_path) == {"_uncaught-syspatch/" + incidents.masked_hash("a fresh traceback")}


def test_non_uncaught_rules_are_never_expired(tmp_path):
    """A patch miss or a tooldesc drift means upstream moved and the repo has
    not caught up. Age is not evidence against it -- it is evidence of
    neglect, and expiring it would delete the only notice."""
    file_incident(tmp_path, "tooldesc-Bash", "a drifted description", at_days_ago=400)
    file_incident(tmp_path, "strip-agent-prohibitions", "an unpatched body", at_days_ago=400)
    gc_patch_failures.expire_transients(tmp_path, retention_days=30, dry_run=False)
    assert len(live_incidents(tmp_path)) == 2, live_incidents(tmp_path)


def test_expired_incident_is_archived_not_deleted(tmp_path):
    digest, _ = file_incident(tmp_path, "_uncaught-syspatch", "a stale traceback", at_days_ago=40)
    gc_patch_failures.expire_transients(tmp_path, retention_days=30, dry_run=False)
    archived = tmp_path / incidents.ARCHIVE_DIRNAME / "_uncaught-syspatch" / f"{digest}.json"
    assert archived.exists(), sorted(tmp_path.rglob("*"))
    assert json.loads(archived.read_text())["rule"] == "_uncaught-syspatch"


def test_expired_then_refired_warns_again(tmp_path):
    """The property that makes expiry safe: a still-live cause re-files after
    expiry, so nothing is lost by assuming a quiet one is spent."""
    body = "a traceback whose cause is still there"
    digest, first = file_incident(tmp_path, "_uncaught-syspatch", body, at_days_ago=40)
    assert first is not None

    assert incidents.save_incident(
        incidents.Incident("_uncaught-syspatch", "SomeError"), digest, tmp_path
    ) is None, "same content must stay deduped while the record is live"

    gc_patch_failures.expire_transients(tmp_path, retention_days=30, dry_run=False)

    refired = incidents.save_incident(
        incidents.Incident("_uncaught-syspatch", "SomeError"), digest, tmp_path
    )
    assert refired is not None, "after expiry a recurring cause must warn again"


def test_dry_run_expires_nothing(tmp_path):
    file_incident(tmp_path, "_uncaught-syspatch", "a stale traceback", at_days_ago=40)
    reported = gc_patch_failures.expire_transients(tmp_path, retention_days=30, dry_run=True)
    assert len(reported) == 1, reported
    assert len(live_incidents(tmp_path)) == 1
