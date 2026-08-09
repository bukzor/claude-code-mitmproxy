#!/usr/bin/env python3
"""Bring log/prompt-captures/ back in step with masks.d/ after a mask edit.

The digest in a capture's filename is `content_hash` of its body under the
masks in force when it was written, so editing masks.d/ leaves the directory
keyed by a hash function that no longer exists: stale names, stale masked
siblings, and bodies that a live proxy would now consider already-captured
under a different name. This re-derives every name, rewrites every masked
sibling, and sets aside the duplicates a coarser mask has merged -- keeping
the earliest-versioned capture of each digest, which is the one syscapture's
first-seen-wins rule would have kept.

Restart the proxy first. A running proxy still masks with the old rules, and
its "already captured?" check is a glob for the digest in the filename -- so
every capture this renames looks new to it, and it re-writes the body under
the old scheme the next time that prompt crosses the wire.

Dry-run by default; `--apply` performs it. Duplicates move to trash/, never
deleted: a capture is a unique historical observation, not a build product."""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

from incidents import content_hash, normalize_body

PROMPTS_DIR = Path(__file__).parent / "log" / "prompt-captures"
TRASH_DIR = Path(__file__).parent / "trash"

NAME_RE = re.compile(r"^(?P<prefix>v[^_]+_.+)_(?P<digest>[0-9a-f]{12})\.raw\.md$")


def plan_directory(directory: Path) -> list[tuple[str, str | None]]:
    """Per capture in name order, its (old base, new base) -- or (old, None)
    when an earlier capture already claimed the recomputed digest. Name order
    is version order, so the survivor is the earliest sighting."""
    claimed: dict[str, str] = {}
    plan: list[tuple[str, str | None]] = []
    for raw in sorted(directory.glob("*.raw.md")):
        m = NAME_RE.match(raw.name)
        assert m, raw
        digest = content_hash(raw.read_text())
        old_base = raw.name.removesuffix(".raw.md")
        if digest in claimed:
            plan.append((old_base, None))
        else:
            new_base = f"{m['prefix']}_{digest}"
            claimed[digest] = new_base
            plan.append((old_base, new_base))
    return plan


def rekey(directory: Path, plan: list[tuple[str, str | None]], trash: Path) -> None:
    """Rename each survivor to its new digest and rewrite its masked sibling;
    move duplicates' raw and masked files to trash."""
    survivors = {new for _, new in plan if new is not None}
    stale = {old for old, new in plan if old != new}
    assert not (survivors & stale), (
        survivors & stale,
        "a new name collides with a capture not yet renamed",
    )

    for old_base, new_base in plan:
        raw = directory / f"{old_base}.raw.md"
        masked = directory / f"{old_base}.md"
        if new_base is None:
            trash.mkdir(parents=True, exist_ok=True)
            raw.rename(trash / raw.name)
            if masked.exists():
                masked.rename(trash / masked.name)
            continue
        if new_base != old_base:
            raw = raw.rename(directory / f"{new_base}.raw.md")
            masked.unlink(missing_ok=True)
        (directory / f"{new_base}.md").write_text(normalize_body(raw.read_text()))


def main():
    args = sys.argv[1:]
    apply = args == ["--apply"]
    assert apply or not args, (args, "usage: rekey_captures.py [--apply]")

    directories = [PROMPTS_DIR] + [d for d in sorted(PROMPTS_DIR.iterdir()) if d.is_dir()]
    for directory in directories:
        plan = plan_directory(directory)
        renamed = [(o, n) for o, n in plan if n is not None and n != o]
        duplicates = [o for o, n in plan if n is None]
        print(
            f"{directory.relative_to(PROMPTS_DIR.parent)}: {len(plan)} captures,"
            f" {len(renamed)} rekeyed, {len(duplicates)} duplicates"
        )
        for old, new in renamed:
            print(f"  rekey {old} -> {new}")
        for old in duplicates:
            print(f"  trash {old}")
        if apply:
            rekey(directory, plan, TRASH_DIR / f"rekeyed-captures-{date.today()}")

    if not apply:
        print("\ndry run; pass --apply to perform")


if __name__ == "__main__":
    main()
