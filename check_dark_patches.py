#!/usr/bin/env python3
"""Per-patch match matrix across promoted fixtures: which patches' match
templates hit which fixture. Match misses are silent by design, so a patch
newly dark on a shape it used to hit is drift the loud path can't see -- run
this whenever a new fixture is promoted (see
design/040-design.kb/loudness-policy.md).

Darkness itself is not asserted: a patch scoped to a shape no promoted fixture
covers is legitimately dark, and only someone reading the table can tell that
from a rule that has quietly died. What *is* asserted is SUBSUMPTION -- a patch
whose match hits the raw fixture but no longer hits once earlier patches (in
load order) have run against it. The real `apply_patches` pipeline runs patches
in sequence against progressively-patched text, so an earlier patch can consume
or alter the very span a later patch's match was written against, and the raw
matrix would still call that later patch a HIT.

`--pattern TEXT` swaps the per-patch rows for a single presence row: "-" (TEXT
absent from the raw fixture), "STRIPPED" (present raw, gone after the full
patch pipeline), or "SURVIVES" (present in both) -- for asking "which shapes
carry this text, and do we already strip it?" before writing a patch. It is a
query, not a check: it prints the row and stops.

Usage: check_dark_patches.py [--data-only] [--pattern TEXT] [FIXTURE ...]

Structure is `verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

import corpus
import syspatch
import templates
import verdict

# The cell vocabulary, in the order a reader should worry about them.
MISS = "-"
HIT = "HIT"
SUBSUMED = "SUBSUMED"


class PatchRow(NamedTuple):
    name: str
    sunset: bool  # upstream_removed: expected to be dark on a current fixture
    cells: dict[str, str]  # fixture stem -> MISS | HIT | SUBSUMED

    @property
    def label(self) -> str:
        return self.name + (" (sunset)" if self.sunset else "")


class PatchMatrix(NamedTuple):
    stems: tuple[str, ...]  # fixture stems, in column order
    rows: tuple[PatchRow, ...]


def fixture_texts(paths: list[Path] | None) -> dict[str, str]:
    """Newline-terminated fixture bodies by stem. Explicit paths are for asking
    the matrix about a candidate before promoting it; the default is every
    promoted fixture."""
    if paths is None:
        return {p.stem: text for p, text in corpus.fixtures().items()}
    texts = {p.stem: p.read_text() for p in paths}
    return {stem: t if t.endswith("\n") else t + "\n" for stem, t in texts.items()}


def collect(paths: list[Path] | None = None) -> PatchMatrix:
    texts = fixture_texts(paths)
    patches = templates.load_rules(syspatch.PATCHES_DIR)
    assert patches, syspatch.PATCHES_DIR

    cells: dict[tuple[str, str], str] = {}
    for stem, raw in texts.items():
        patched_so_far = raw
        for patch in patches:
            if templates.first_hit(raw, patch.matches) is None:
                cells[stem, patch.name] = MISS
            elif templates.first_hit(patched_so_far, patch.matches) is not None:
                cells[stem, patch.name] = HIT
            else:
                cells[stem, patch.name] = SUBSUMED
            if not patch.upstream_removed:
                # Advance the chain one patch at a time, mirroring
                # apply_patches' own sequential loop, so later patches see what
                # they'd really see. Skipped for upstream-removed patches: they
                # never modify text (see apply_patches), and replaying them here
                # only emits "matched-despite-upstream-removed" -- expected on
                # any pre-removal fixture (see `corpus.latest_fixture`), not a
                # defect this matrix is trying to surface.
                patched_so_far = syspatch.apply_patches(
                    patched_so_far, (patch,), capture_dir=None
                )

    return PatchMatrix(
        tuple(texts),
        tuple(
            PatchRow(
                patch.name,
                patch.upstream_removed,
                {stem: cells[stem, patch.name] for stem in texts},
            )
            for patch in patches
        ),
    )


def table(stems: tuple[str, ...], rows: list[tuple[str, dict[str, str]]]) -> str:
    width = {s: max(len(s), max(len(row[s]) for _, row in rows)) for s in stems}
    label_width = max(len(label) for label, _ in rows)
    out = [" " * label_width + "".join(f"  {s:>{width[s]}}" for s in stems)]
    for label, row in rows:
        cells = "".join(f"  {row[stem]:>{width[stem]}}" for stem in stems)
        out.append(f"{label:{label_width}}{cells}")
    return "\n".join(out) + "\n"


def render(matrix: PatchMatrix) -> str:
    return table(matrix.stems, [(row.label, row.cells) for row in matrix.rows])


def subsumed_patches(matrix: PatchMatrix) -> dict[str, list[str]]:
    """patches an earlier patch has already consumed. A patch whose match hits
    the raw fixture but not the text its turn actually sees is dead in
    practice, and dead silently: a match miss is how a rule reports its own
    irrelevance, so nothing at proxy time distinguishes "not applicable here"
    from "someone else got there first".

    Sunset rows are exempt: an upstream-removed rule asserts that text is gone,
    and on a fixture that predates the removal our own earlier patch deleting
    it first is the expected reading, not a defect."""
    subsumed = {
        row.name: [stem for stem, cell in row.cells.items() if cell == SUBSUMED]
        for row in matrix.rows
        if not row.sunset
    }
    return {name: stems for name, stems in subsumed.items() if stems}


PREDICATES = (subsumed_patches,)


def pattern_cell(pattern: str, raw: str, patched: str) -> str:
    if pattern not in raw:
        return MISS
    return "SURVIVES" if pattern in patched else "STRIPPED"


def pattern_row(pattern: str, paths: list[Path] | None) -> str:
    """Where a literal text lives, and whether the patch set already removes
    it. The full live patch set at once, unlike the matrix: the question is
    what a session ends up with, not which rule did it."""
    texts = fixture_texts(paths)
    live = tuple(p for p in templates.load_rules(syspatch.PATCHES_DIR) if not p.upstream_removed)
    row = {
        stem: pattern_cell(pattern, raw, syspatch.apply_patches(raw, live, capture_dir=None))
        for stem, raw in texts.items()
    }
    return table(tuple(texts), [(repr(pattern), row)])


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pattern = None
    if "--pattern" in argv:
        at = argv.index("--pattern")
        assert len(argv) > at + 1, "--pattern requires a value"
        pattern = argv[at + 1]
        del argv[at : at + 2]
    paths = [Path(arg) for arg in argv if not arg.startswith("-")] or None

    if pattern is not None:
        sys.stdout.write(pattern_row(pattern, paths))
        return 0
    return verdict.run(lambda: collect(paths), render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
