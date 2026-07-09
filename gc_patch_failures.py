#!/usr/bin/env python3
"""Prune patch-failures/_archive/ entries older than a retention window.

incidents.archive_incident moves resolved incidents out of the live rule
dirs into _archive/ instead of deleting them outright, so a just-resolved
incident stays inspectable for a while. This is the other half: reclaim
disk from archived entries nobody came back to look at. Age is read from
each file's mtime, which archive_incident resets to the archive time (not
the incident's original `at` timestamp).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from incidents import ARCHIVE_DIRNAME, CAPTURE_DIR

DEFAULT_RETENTION_DAYS = 30


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


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv[1:]
    retention_days = float(args[0]) if args else DEFAULT_RETENTION_DAYS

    removed = gc(CAPTURE_DIR / ARCHIVE_DIRNAME, retention_days, dry_run=dry_run)

    verb = "would remove" if dry_run else "removed"
    for path in removed:
        print(f"{verb}: {path}")
    print(f"{verb} {len(removed)} file(s) older than {retention_days:g}d", file=sys.stderr)


if __name__ == "__main__":
    main()
