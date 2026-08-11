#!/usr/bin/env python3
"""Offline validation of the algebra the capture keys rest on: the laws
`keying.claims.kb/quotient.kb/` states, checked against every body on disk.

These are the properties that make a masked digest mean "same content modulo
session noise" and a core digest mean "same prompt copy". Nothing at proxy
time notices when one stops holding: a broken law yields a well-formed digest
that answers a different question than the one asked. This is the detector.

Usage: check_laws.py -- asserts every law; any output but `ok` lines is a
failure.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import incidents
import templates

CAPTURES_DIR = Path(__file__).parent / "log" / "prompt-captures"
KB_DIR = Path(__file__).parent / "system-prompts.kb"
BLOCKS_DIR = Path(__file__).parent / "blocks.d"


def load_corpus() -> dict[str, str]:
    """Every body the laws are checked against: captures (what upstream
    actually sent) plus promoted fixtures (what patches are validated on).
    Subagent captures are included -- they are masked by the same rules and
    are where overlapping-span bugs have shown up first."""
    bodies = {
        str(p): p.read_text() for p in sorted(CAPTURES_DIR.rglob("*.raw.md"))
    }
    bodies.update({
        str(p): p.read_text()
        for p in sorted(KB_DIR.glob("*.md"))
        if p.name != "CLAUDE.md"
    })
    assert bodies, (CAPTURES_DIR, KB_DIR, "no bodies to check")
    return bodies


def check_idempotent(bodies: dict[str, str], masks) -> None:
    """Masking twice equals masking once, so a masked body and a raw one
    agree on their digest and re-masking a `.md` sibling is a no-op."""
    bad = [
        name
        for name, body in bodies.items()
        if templates.apply_masks(templates.apply_masks(body, masks), masks)
        != templates.apply_masks(body, masks)
    ]
    assert not bad, (bad[:3], "masking is not idempotent")
    print(f"idempotent      ok  {len(bodies)} bodies")


def check_monotone(bodies: dict[str, str], masks) -> None:
    """Adding a mask only ever merges equivalence classes, never splits one.
    A mask that split a class would mean two bodies the old rules called the
    same are now different, which no mask can honestly report: masks delete
    session-specific detail, and deleting cannot create a distinction."""
    full = {k: templates.apply_masks(v, masks) for k, v in bodies.items()}
    for dropped in masks:
        fewer = tuple(m for m in masks if m.name != dropped.name)
        small = {k: templates.apply_masks(v, fewer) for k, v in bodies.items()}
        split = [
            (a, b)
            for a, b in itertools.combinations(bodies, 2)
            if small[a] == small[b] and full[a] != full[b]
        ]
        assert not split, (dropped.name, split[:2], "adding a mask split a class")
    print(f"monotone        ok  {len(masks)} masks")


def block_spans(text: str, blocks) -> dict[str, list[tuple[int, int]]]:
    """Where each block rule would delete, measured against the text every
    rule sees first. `strip_blocks` deletes every occurrence, so a rule's
    footprint is all of its matches, not just the first."""
    return {
        block.name: [
            m.span()
            for m in templates.template_to_regex(block.template).finditer(text)
        ]
        for block in blocks
    }


def overlapping_blocks(spans: dict[str, list[tuple[int, int]]]) -> set[str]:
    """Names of the rules whose deletion span overlaps another rule's."""
    overlapping: set[str] = set()
    for (a, a_spans), (b, b_spans) in itertools.combinations(spans.items(), 2):
        if any(
            a0 < b1 and b0 < a1 for a0, a1 in a_spans for b0, b1 in b_spans
        ):
            overlapping.update((a, b))
    return overlapping


def check_blocks_disjoint(bodies: dict[str, str], blocks) -> None:
    """No two block rules may delete overlapping bytes.

    Disjoint deletions commute, so this one property carries both halves of
    what `blocks.d/README.md` promises: the stripped text is the same whatever
    order the directory loads in -- that order is alphabetical and carries no
    meaning, so a core digest moving with it would be an artifact of a
    filename -- and the reported flags name every rule that was really there
    rather than whichever ran first.

    Asserted, not warned about. Overlap is how a rule once took credit for a
    section it never matched, and the placeholder that let it reach that far
    is gone; a fresh overlap means the reach came back by another route.
    """
    for name, body in sorted(bodies.items()):
        masked, _ = templates.borrow_newline(incidents.normalize_body(body))
        overlapping = overlapping_blocks(block_spans(masked, blocks))
        assert not overlapping, (name, sorted(overlapping), "block spans overlap")
    print(f"blocks disjoint ok  {len(bodies)} bodies")


def main() -> None:
    bodies = load_corpus()
    masks = incidents.masks()
    blocks = templates.load_templates(BLOCKS_DIR)
    check_idempotent(bodies, masks)
    check_monotone(bodies, masks)
    check_blocks_disjoint(bodies, blocks)


if __name__ == "__main__":
    main()
