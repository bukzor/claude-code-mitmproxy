#!/usr/bin/env python3
"""Offline validation of the algebra the capture keys rest on: the laws
`keying.claims.kb/quotient.kb/` states, checked against every body on disk.

These are the properties that make a masked digest mean "same content modulo
session noise" and a core digest mean "same prompt copy". Nothing at proxy
time notices when one stops holding: a broken law yields a well-formed digest
that answers a different question than the one asked. This is the detector.

Usage: check_laws.py -- asserts the laws that must hold, warns about the
divergence that is still an open design question (block flags, see
`keying.claims.kb/this-proxy.kb/`).
"""
from __future__ import annotations

import itertools
from pathlib import Path

import incidents
import templates

CAPTURES_DIR = Path(__file__).parent / "log" / "prompt-captures"
KB_DIR = Path(__file__).parent / "system-prompts.kb"
BLOCKS_DIR = Path(__file__).parent / "blocks.d"

# Orders are enumerated over the overlapping rules only, so this bounds a
# factorial. Tripping it means blocks have grown genuinely tangled, which is
# news in itself and should stop the check rather than degrade it to a sample.
MAX_CONTESTED = 5


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


def contested_blocks(spans: dict[str, list[tuple[int, int]]]) -> set[str]:
    """Names of the rules whose deletion span overlaps another rule's.

    Rules with disjoint spans commute outright: deleting disjoint substrings
    removes the same bytes and credits the same rules whatever the order. So
    the contested rules are the *only* ones whose relative order can change
    anything, which is what lets the check below enumerate orders exhaustively
    instead of sampling them. A sample here would be the very thing this file
    exists to rule out -- a check that can pass while the law is false.
    """
    contested: set[str] = set()
    for (a, a_spans), (b, b_spans) in itertools.combinations(spans.items(), 2):
        if any(
            a0 < b1 and b0 < a1 for a0, a1 in a_spans for b0, b1 in b_spans
        ):
            contested.update((a, b))
    return contested


def check_block_confluence(bodies: dict[str, str], blocks) -> None:
    """Block stripping must not depend on the order the blocks load in: that
    order is alphabetical and carries no meaning, so a core digest that moved
    with it would be an artifact of a filename.

    The stripped text is asserted. Which rules report having fired is only
    warned about: where spans overlap, whichever rule runs first takes the
    credit, and choosing the fix is an open design question.
    """
    contested_bodies = 0
    flag_divergent = []
    for name, body in sorted(bodies.items()):
        masked = incidents.normalize_body(body)
        borrowed, _ = templates.borrow_newline(masked)
        contested = contested_blocks(block_spans(borrowed, blocks))
        if not contested:
            continue
        contested_bodies += 1
        head = tuple(b for b in blocks if b.name in contested)
        rest = tuple(b for b in blocks if b.name not in contested)
        assert len(head) <= MAX_CONTESTED, (name, contested, "too many to enumerate")
        base_text, base_present = templates.strip_blocks(masked, blocks)
        for order in itertools.permutations(head):
            text, present = templates.strip_blocks(masked, order + rest)
            assert text == base_text, (
                name, [b.name for b in order], "core digest depends on block order"
            )
            if sorted(present) != sorted(base_present):
                flag_divergent.append((name, sorted(contested)))
                break
    print(
        f"block confluence ok  {len(bodies)} bodies, "
        f"{contested_bodies} with overlapping spans"
    )
    report_flag_divergence(flag_divergent, len(bodies))


def report_flag_divergence(divergent: list, total: int) -> None:
    """Not an assertion: the stripped text is right, only the reported rule
    names are ambiguous, and the choice between bounding the block pattern,
    forbidding overlap, and reporting all claimants is unmade."""
    if not divergent:
        return
    print(
        f"WARNING: block flags depend on load order for {len(divergent)} of "
        f"{total} bodies; see keying.claims.kb/this-proxy.kb/"
        f"block-flags-are-an-artifact.md"
    )
    for name, contested in divergent[:3]:
        print(f"  {','.join(contested)}  {Path(name).name}")


def main() -> None:
    bodies = load_corpus()
    masks = incidents.masks()
    blocks = templates.load_templates(BLOCKS_DIR)
    check_idempotent(bodies, masks)
    check_monotone(bodies, masks)
    check_block_confluence(bodies, blocks)


if __name__ == "__main__":
    main()
