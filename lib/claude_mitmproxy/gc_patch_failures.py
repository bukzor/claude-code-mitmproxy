#!/usr/bin/env python3
"""Age out incidents nobody is going to act on, in two places.

incidents.archive_incident moves resolved incidents out of the live rule
dirs into _archive/ instead of deleting them outright, so a just-resolved
incident stays inspectable for a while. `gc` is the other half: reclaim
disk from archived entries nobody came back to look at. Age is read from
each file's mtime, which archive_incident resets to the archive time (not
the incident's original `at` timestamp).

`expire_transients` archives in the first place, for the one rule family
whose incidents routinely have no cause left to find: `_uncaught-*`. A
live-edit transient and a standing bug in an addon hook look identical at
capture time and are told apart only by waiting, so waiting is what this
does -- and a human never has to hold the question.

Nothing is lost by guessing "spent" wrong, which is what makes the guess
safe to automate: `save_incident` is idempotent per (rule, content), so
removing the record restores the warning. A cause that is still live
re-files and re-warns on its very next request; a transient never returns.
That argument covers `_uncaught-*` only. A patch miss or a tooldesc drift
means upstream moved and this repo has not caught up -- the record's age is
evidence of neglect, not of resolution, and expiring it would delete the
only notice.

Neither half is scheduled by anyone: `sweep_at_startup` runs both from
`addons/syspatch.py`'s load hook, once per proxy start. Running it by hand
stays safe and does the same thing, but nothing depends on someone doing so.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from claude_mitmproxy import incidents

DEFAULT_RETENTION_DAYS = 30

# Rules whose incidents may expire unread. The prefix is the addon-hook
# wrapper's (`incidents.capture_uncaught`), so this covers every addon
# without naming them.
TRANSIENT_RULE_PREFIX = "_uncaught-"

FAILURE_RULE = "_gc-patch-failures"


def gc(archive_dir: Path, retention_days: float, *, dry_run: bool) -> list[Path]:
    """Delete files under archive_dir older than retention_days, then prune
    any rule directories left empty. Returns the files removed (or, under
    dry_run, that would be)."""
    if not archive_dir.exists():
        return []

    cutoff = time.time() - retention_days * 86400
    removed = [
        path
        for path in archive_dir.rglob("*")
        if path.is_file() and path.stat().st_mtime < cutoff
    ]
    if not dry_run:
        for path in removed:
            path.unlink()
        for rule_dir in sorted(archive_dir.iterdir(), reverse=True):
            if rule_dir.is_dir() and not any(rule_dir.iterdir()):
                rule_dir.rmdir()
    return removed


def expire_transients(
    capture_dir: Path, retention_days: float, *, dry_run: bool
) -> list[Path]:
    """Archive `_uncaught-*` incidents whose record is older than
    retention_days. Returns the incident files archived (or, under dry_run,
    that would be).

    Archived rather than deleted, so `gc` still gets its own look at them
    later and the evidence survives one more window -- an expiry that
    guessed wrong is then still readable next to the re-filed record."""
    if not capture_dir.exists():
        return []

    cutoff = time.time() - retention_days * 86400
    stale = sorted(
        path
        for rule_dir in capture_dir.iterdir()
        if rule_dir.is_dir() and rule_dir.name.startswith(TRANSIENT_RULE_PREFIX)
        for path in rule_dir.glob("*.json")
        if path.stat().st_mtime < cutoff
    )
    if not dry_run:
        for path in stale:
            incidents.archive_incident(path.parent.name, path.stem, capture_dir)
    return stale


def sweep(retention_days: float, *, dry_run: bool) -> tuple[list[Path], list[Path]]:
    """Both halves against the live store, as (expired, removed).

    Expiry runs first, so an incident that ages out today is archived now and
    judged by the archive window on some later run -- never expired and
    reclaimed in the same pass, which would collapse the two windows into one
    and lose the inspectable interval the archive exists to provide."""
    expired = expire_transients(incidents.CAPTURE_DIR, retention_days, dry_run=dry_run)
    archive = incidents.CAPTURE_DIR / incidents.ARCHIVE_DIRNAME
    removed = gc(archive, retention_days, dry_run=dry_run)
    return expired, removed


def sweep_at_startup() -> None:
    """Run the sweep once, from `addons/syspatch.py`'s load hook -- this
    module's only scheduler, and the reason nobody has to remember it.

    A proxy start is the right occasion on both counts: once per process, so
    it never touches the request path, and frequent enough against a window
    measured in weeks (the proxy is restarted on the order of days).

    Failures are captured, not raised. Everything here is disk housekeeping,
    and a proxy that patches traffic with a cluttered `log/` is strictly
    better than one that refused to start over it. The incident is the notice,
    which does mean a store too broken to record it takes the proxy down --
    correctly, since at that point nothing in this repo can report anything."""
    try:
        expired, removed = sweep(DEFAULT_RETENTION_DAYS, dry_run=False)
    except Exception as exc:
        incidents.capture_uncaught(FAILURE_RULE, exc, incidents.CAPTURE_DIR)
        return
    # Silent when it did nothing, which is most starts: an unconditional line
    # would be one nobody reads, and this one should be worth reading.
    if expired or removed:
        logging.info(
            "gc: expired %d transient(s), reclaimed %d archived file(s)",
            len(expired),
            len(removed),
        )


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv[1:]
    retention_days = float(args[0]) if args else DEFAULT_RETENTION_DAYS

    expired, removed = sweep(retention_days, dry_run=dry_run)

    verb = "would expire" if dry_run else "expired"
    for path in expired:
        print(f"{verb}: {path}")
    verb = "would remove" if dry_run else "removed"
    for path in removed:
        print(f"{verb}: {path}")
    print(
        f"expired {len(expired)} transient(s), {verb} {len(removed)} archived file(s)"
        f" older than {retention_days:g}d",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
