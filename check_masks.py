#!/usr/bin/env python3
"""Which committed fixtures each capture-digest mask matches, and whether the
masks still keep distinct prompts distinct.

A mask that stops matching is invisible in production -- masks are silent by
construction (`masks.d/README.md`), so the only symptom is every session
minting a fresh digest, which nobody watches. Read this after editing
`masks.d/` or promoting a fixture.

Usage: check_masks.py [--data-only]
  --data-only  the table alone, for diffing two runs against each other

Structure is `verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

from typing import NamedTuple

import corpus
import incidents
import templates
import verdict


class MaskRow(NamedTuple):
    name: str
    hits: tuple[str, ...]  # stems of the fixtures this mask matched


class MaskMatrix(NamedTuple):
    rows: tuple[MaskRow, ...]
    by_digest: dict[str, tuple[str, ...]]  # masked digest -> fixture stems


def collect() -> MaskMatrix:
    texts = corpus.fixtures()
    rows = []
    for mask in incidents.masks():
        pattern = templates.template_to_regex(mask.template)
        rows.append(MaskRow(
            mask.name,
            tuple(p.stem for p, text in texts.items() if pattern.search(text)),
        ))

    by_digest: dict[str, list[str]] = {}
    for path, text in texts.items():
        digest = incidents.digest_of(incidents.normalize_body(text))
        by_digest.setdefault(digest, []).append(path.stem)
    return MaskMatrix(tuple(rows), {d: tuple(s) for d, s in by_digest.items()})


def render(matrix: MaskMatrix) -> str:
    out = [f"{row.name:24} {len(row.hits):3} {' '.join(row.hits)}" for row in matrix.rows]
    fixtures = sum(len(stems) for stems in matrix.by_digest.values())
    out.append(f"\n{fixtures} fixtures, {len(matrix.by_digest)} distinct digests")
    return "\n".join(out) + "\n"


def dark_masks(matrix: MaskMatrix) -> list[str]:
    """masks matching no committed fixture. Either the prose they target
    drifted upstream, or no promoted fixture exercises them. Unlike a dark
    patch this is never legitimate: a mask has no `match` scope it can be
    out of, so finding nothing means it is doing nothing."""
    return [row.name for row in matrix.rows if not row.hits]


def collapsed_fixtures(matrix: MaskMatrix) -> dict[str, tuple[str, ...]]:
    """fixtures sharing a masked digest. Every fixture is a distinct prompt
    body, so a collision means a mask swallowed real prompt copy -- e.g. a
    model-id placeholder wide enough to erase the difference between two
    models' prompts."""
    return {d: stems for d, stems in matrix.by_digest.items() if len(stems) > 1}


PREDICATES = (dark_masks, collapsed_fixtures)


def main(argv: list[str] | None = None) -> int:
    return verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
