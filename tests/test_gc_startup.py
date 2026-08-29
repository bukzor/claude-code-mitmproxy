"""The sweep runs itself: once per proxy start, from an addon's load hook.

`gc_patch_failures.py` has no scheduler and never had one -- "run it
occasionally" was a duty on a human. A proxy start is the natural occasion:
once per process, off the request path, and frequent enough against a
retention window measured in weeks.

It must not take the proxy down, though. Stale files on disk have no bearing
on whether traffic gets patched, so a sweep that fails files an incident and
lets the proxy come up.
"""

from __future__ import annotations

import os
import time

from claude_mitmproxy import gc_patch_failures
from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_patches
from claude_mitmproxy.addons import syspatch


def age(path, days):
    old = time.time() - days * 86400
    os.utime(path, (old, old))


def test_startup_sweep_does_both_halves(tmp_path, monkeypatch):
    monkeypatch.setattr(incidents, "CAPTURE_DIR", tmp_path)

    transient = tmp_path / "_uncaught-syspatch" / "aaaaaaaaaaaa.json"
    transient.parent.mkdir(parents=True)
    transient.write_text("{}")
    age(transient, 40)

    archived = tmp_path / incidents.ARCHIVE_DIRNAME / "tooldesc-Bash" / "bbb.json"
    archived.parent.mkdir(parents=True)
    archived.write_text("{}")
    age(archived, 40)

    gc_patch_failures.sweep_at_startup()

    assert not transient.exists(), "stale transient should have been expired"
    assert not archived.exists(), "stale archived file should have been reclaimed"


def test_startup_sweep_reports_its_own_failure(tmp_path, monkeypatch):
    """A broken sweep is an incident, not an outage: the proxy patches traffic
    just as well with a full log/ dir, so refusing to start would trade a real
    capability for a housekeeping one."""
    monkeypatch.setattr(incidents, "CAPTURE_DIR", tmp_path)
    # Injected rather than provoked: every real way to make the sweep throw
    # (unreadable dir, undeletable file) is a chmod that root ignores.
    monkeypatch.setattr(
        gc_patch_failures,
        "gc",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("disk on fire")),
    )

    gc_patch_failures.sweep_at_startup()

    filed = sorted((tmp_path / gc_patch_failures.FAILURE_RULE).glob("*.json"))
    assert len(filed) == 1, sorted(tmp_path.rglob("*"))
    (body,) = (tmp_path / incidents.BODIES_DIRNAME).glob("*.md")
    assert "disk on fire" in body.read_text()


def test_load_hook_sweeps(tmp_path, monkeypatch):
    """The wiring itself: nothing else calls this, so a dropped line would
    silently restore the manual duty."""
    # A real (if pointless) patch dir: `load_rules` treats an empty one as a
    # wrong-$HOME config error, which would red this test for the wrong reason.
    patch = tmp_path / "strip-something"
    patch.mkdir()
    (patch / "match.md").write_text("some text\n")
    (patch / "replace.md").write_text("\n")
    monkeypatch.setattr(prompt_patches, "PATCHES_DIR", tmp_path)
    called = []
    monkeypatch.setattr(gc_patch_failures, "sweep_at_startup", lambda: called.append(1))

    syspatch.load(None)

    assert called == [1]
