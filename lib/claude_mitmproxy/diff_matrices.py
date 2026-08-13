#!/usr/bin/env python3
"""Diff two per-patch match matrices, reporting only cells that changed.

Rows and columns come and go between runs -- a promoted fixture adds a
column, a retired patch drops a row -- and those differences are not what
the diff is for. Only the intersection is compared; what only one side has
is listed as unshared and left alone.

Both sides are `check_dark_patches.PatchMatrix`: the tool that emits the
matrix owns the type and its `parse`, so this one never learns the layout.
A cell here is the same object the check asserts on, not a substring that
happened to line up.

Usage: diff_matrices.py BEFORE.txt AFTER.txt
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

from claude_mitmproxy import check_dark_patches


class CellChange(NamedTuple):
    patch: str
    stem: str  # fixture
    before: str
    after: str


class MatrixDiff(NamedTuple):
    cells: tuple[CellChange, ...]
    sunset: tuple[str, ...]  # patches whose upstream-removed flag moved
    shared_patches: int
    shared_stems: int
    unshared_patches: tuple[str, ...]
    unshared_stems: tuple[str, ...]


def diff(before: check_dark_patches.PatchMatrix, after: check_dark_patches.PatchMatrix) -> MatrixDiff:
    a = {row.name: row for row in before.rows}
    b = {row.name: row for row in after.rows}
    shared = sorted(a.keys() & b.keys())
    stems = sorted(set(before.stems) & set(after.stems))
    return MatrixDiff(
        cells=tuple(
            CellChange(name, stem, a[name].cells[stem], b[name].cells[stem])
            for name in shared
            for stem in stems
            if a[name].cells[stem] != b[name].cells[stem]
        ),
        sunset=tuple(name for name in shared if a[name].sunset != b[name].sunset),
        shared_patches=len(shared),
        shared_stems=len(stems),
        unshared_patches=tuple(sorted(a.keys() ^ b.keys())),
        unshared_stems=tuple(sorted(set(before.stems) ^ set(after.stems))),
    )


def render(result: MatrixDiff) -> str:
    out = [f"{c.patch} {c.stem}: {c.before} -> {c.after}" for c in result.cells]
    out += [f"{name}: sunset flag moved" for name in result.sunset]
    out.append(f"compared {result.shared_patches} patches x {result.shared_stems} fixtures")
    if result.unshared_patches:
        out.append("  unshared patches: " + ", ".join(result.unshared_patches))
    if result.unshared_stems:
        out.append("  unshared fixtures: " + ", ".join(result.unshared_stems))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    assert len(argv) == 2, "usage: diff_matrices.py BEFORE.txt AFTER.txt"
    before, after = (check_dark_patches.parse(Path(arg).read_text()) for arg in argv)
    sys.stdout.write(render(diff(before, after)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
