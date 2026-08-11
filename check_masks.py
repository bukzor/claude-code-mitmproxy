#!/usr/bin/env python3
"""Verify every capture-digest mask still matches committed text, and that
masking is idempotent and injective enough to keep distinct prompts distinct.

A mask that stops matching is invisible in production -- masks are silent by
construction (see masks.d/README.md), so the only symptom is every session
minting a fresh digest, which nobody watches. This is where that gets caught:
run it after editing masks.d/ or promoting a fixture."""
from __future__ import annotations

import sys
from pathlib import Path

import incidents
import templates

KB_DIR = Path("system-prompts.kb")


def main():
    fixtures = sorted(p for p in KB_DIR.glob("*.md") if p.name != "CLAUDE.md")
    assert fixtures, KB_DIR
    # Templates ending "\n" need end-of-body to read as a line boundary --
    # the same normalization apply_masks does before matching.
    texts = {p: p.read_text() for p in fixtures}
    texts = {p: t if t.endswith("\n") else t + "\n" for p, t in texts.items()}

    unwitnessed = []
    for mask in templates.load_templates(incidents.MASKS_DIR):
        pattern = templates.template_to_regex(mask.template)
        hits = [p for p, text in texts.items() if pattern.search(text)]
        if not hits:
            unwitnessed.append(mask.name)
        print(f"{mask.name:24} {len(hits):3} {' '.join(p.stem for p in hits)}")
    assert not unwitnessed, (
        unwitnessed,
        "mask matches no committed fixture: either its prose drifted upstream, "
        "or promote a fixture that exercises it",
    )

    masked = {p: incidents.normalize_body(text) for p, text in texts.items()}
    for path, text in masked.items():
        # The replacement is the template verbatim, so a mask matches its own
        # output; a second pass that changes anything means some mask isn't
        # the identity rewrite the format promises.
        assert incidents.normalize_body(text) == text, (
            path,
            "masking is not idempotent",
        )

    by_digest: dict[str, list[Path]] = {}
    for path, text in masked.items():
        by_digest.setdefault(incidents.digest_of(text), []).append(path)
    collisions = {d: ps for d, ps in by_digest.items() if len(ps) > 1}
    # Every fixture is a distinct prompt body, so a shared digest means a mask
    # swallowed real prompt copy -- e.g. a model-id placeholder wide enough to
    # erase the difference between two models' prompts.
    assert not collisions, (collisions, "masks collapse distinct fixtures")

    print(f"\n{len(fixtures)} fixtures, {len(by_digest)} distinct digests")


if __name__ == "__main__":
    main()
