#!/usr/bin/env python3
"""Offline validation of the algebra the capture keys rest on: the laws
`keying.claims.kb/quotient.kb/` states, checked against every body on disk.

These are the properties that make a masked digest mean "same content modulo
session noise" and a core digest mean "same prompt copy". Nothing at proxy
time notices when one stops holding: a broken law yields a well-formed digest
that answers a different question than the one asked. This is the detector.

Usage: check_laws.py [--data-only]

Structure is `verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

import itertools
from typing import NamedTuple

import corpus
import incidents
import syspatch
import templates
import verdict


class Corpus(NamedTuple):
    """The bodies the laws must hold over, and the rule sets they constrain."""

    captures: dict[str, str]
    fixtures: dict[str, str]
    masks: tuple[templates.Template, ...]
    blocks: tuple[templates.Template, ...]

    @property
    def bodies(self) -> dict[str, str]:
        return {**self.captures, **self.fixtures}


def collect() -> Corpus:
    found = Corpus(
        captures=corpus.capture_bodies(),
        fixtures={str(p): text for p, text in corpus.fixtures().items()},
        masks=incidents.masks(),
        blocks=templates.load_templates(syspatch.BLOCKS_DIR),
    )
    assert found.bodies, "no bodies to check"
    return found


def render(found: Corpus) -> str:
    """The corpus, since its size is the thing a green run is silent about."""
    return (
        f"{len(found.bodies)} bodies"
        f" ({len(found.captures)} captures, {len(found.fixtures)} fixtures)"
        f", {len(found.masks)} masks, {len(found.blocks)} blocks\n"
    )


def not_idempotent(found: Corpus) -> list[str]:
    """bodies whose second masking differs from the first. Masking twice must
    equal masking once, so that a masked body and a raw one agree on their
    digest and re-masking a `.md` sibling is a no-op."""
    once = {name: templates.apply_masks(body, found.masks) for name, body in found.bodies.items()}
    return [
        name
        for name, masked in once.items()
        if templates.apply_masks(masked, found.masks) != masked
    ]


def masks_that_split_a_class(found: Corpus) -> dict[str, list[tuple[str, str]]]:
    """masks that tell two bodies apart that the other masks call the same.
    Adding a mask may only merge equivalence classes: masks delete
    session-specific detail, and deleting cannot create a distinction."""
    bodies = found.bodies
    full = {k: templates.apply_masks(v, found.masks) for k, v in bodies.items()}
    splits = {}
    for dropped in found.masks:
        fewer = tuple(m for m in found.masks if m.name != dropped.name)
        small = {k: templates.apply_masks(v, fewer) for k, v in bodies.items()}
        split = [
            (a, b)
            for a, b in itertools.combinations(bodies, 2)
            if small[a] == small[b] and full[a] != full[b]
        ]
        if split:
            splits[dropped.name] = split[:2]
    return splits


def block_spans(text: str, blocks) -> dict[str, list[tuple[int, int]]]:
    """Where each block rule would delete, measured against the text every
    rule sees first. `strip_blocks` deletes every occurrence, so a rule's
    footprint is all of its matches, not just the first."""
    return {
        block.name: [
            m.span() for m in templates.template_to_regex(block.template).finditer(text)
        ]
        for block in blocks
    }


def overlapping_blocks(spans: dict[str, list[tuple[int, int]]]) -> set[str]:
    """Names of the rules whose deletion span overlaps another rule's."""
    overlapping: set[str] = set()
    for (a, a_spans), (b, b_spans) in itertools.combinations(spans.items(), 2):
        if any(a0 < b1 and b0 < a1 for a0, a1 in a_spans for b0, b1 in b_spans):
            overlapping.update((a, b))
    return overlapping


def bodies_with_overlapping_blocks(found: Corpus) -> dict[str, list[str]]:
    """bodies where two block rules delete overlapping bytes.

    Disjoint deletions commute, so this one property carries both halves of
    what `blocks.d/README.md` promises: the stripped text is the same whatever
    order the directory loads in -- that order is alphabetical and carries no
    meaning, so a core digest moving with it would be an artifact of a
    filename -- and the reported flags name every rule that was really there
    rather than whichever ran first.

    Overlap is how a rule once took credit for a section it never matched, and
    the placeholder that let it reach that far is gone; a fresh overlap means
    the reach came back by another route.
    """
    found_overlaps = {}
    for name, body in sorted(found.bodies.items()):
        masked, _ = templates.borrow_newline(incidents.normalize_body(body))
        overlapping = overlapping_blocks(block_spans(masked, found.blocks))
        if overlapping:
            found_overlaps[name] = sorted(overlapping)
    return found_overlaps


PREDICATES = (not_idempotent, masks_that_split_a_class, bodies_with_overlapping_blocks)


def main(argv: list[str] | None = None) -> int:
    return verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
