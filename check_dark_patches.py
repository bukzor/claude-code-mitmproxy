#!/usr/bin/env python3
"""Per-patch match matrix across captured fixtures: which patches' match
templates hit which capture. Match misses are silent by design, so a patch
newly dark on a shape it used to hit is drift the loud path can't see —
run this whenever a new capture is promoted (see
design/040-design.kb/loudness-policy.md).

Also flags SUBSUMPTION: a patch whose match hits the raw capture but no
longer hits once earlier patches (in load order) have already run against
it -- the real `apply_patches` pipeline runs patches in sequence against
progressively-patched text, so an earlier patch can silently consume or
alter the very span a later patch's match was written against. Raw-HIT +
patched-MISS means that later patch is dead in practice even though this
tool's raw-only check used to call it HIT."""
from __future__ import annotations

import sys
from pathlib import Path

from syspatch import PATCHES_DIR, _first_hit, apply_patches, load_patches

KB_DIR = Path("system-prompts.kb")


def main():
    fixtures = [Path(arg) for arg in sys.argv[1:]] or sorted(
        p for p in KB_DIR.iterdir() if p.suffix == ".md" and p.name != "CLAUDE.md"
    )
    # Templates ending "\n" need end-of-body to read as a line boundary --
    # the same normalization apply_patches does before matching. Without it,
    # a block at end-of-body shows as a false match miss here.
    texts = {fixture: fixture.read_text() for fixture in fixtures}
    texts = {f: t if t.endswith("\n") else t + "\n" for f, t in texts.items()}
    patches = load_patches(PATCHES_DIR)
    assert patches, PATCHES_DIR

    # cells[fixture, patch.name]: "-" (raw match miss, patch not applicable
    # here), "HIT" (applies for real, in pipeline order), or "SUBSUMED" (raw
    # match hit, but an earlier patch already altered the text so this
    # patch's match no longer hits by the time its turn comes in the real
    # pipeline).
    cells: dict[tuple[Path, str], str] = {}
    for fixture in fixtures:
        patched_so_far = texts[fixture]
        for patch in patches:
            if _first_hit(texts[fixture], patch.matches) is None:
                cells[fixture, patch.name] = "-"
            elif _first_hit(patched_so_far, patch.matches) is not None:
                cells[fixture, patch.name] = "HIT"
            else:
                cells[fixture, patch.name] = "SUBSUMED"
            if not patch.upstream_removed:
                # Advance the chain one patch at a time, mirroring
                # apply_patches' own sequential loop, so later patches see
                # what they'd really see. Skip this for upstream-removed
                # patches: they never modify text (see apply_patches), and
                # replaying them here only emits "matched-despite-upstream-
                # removed" -- expected on any pre-removal fixture (see
                # check_patches.py's latest_capture docstring), not a defect
                # this matrix is trying to surface.
                patched_so_far = apply_patches(patched_so_far, (patch,), capture_dir=None)

    col_width = {f: max(len(f.stem), len("SUBSUMED")) for f in fixtures}
    label_width = max(len(p.name) for p in patches) + len(" (sunset)")
    print(" " * label_width + "".join(f"  {f.stem:>{col_width[f]}}" for f in fixtures))
    for patch in patches:
        label = patch.name + (" (sunset)" if patch.upstream_removed else "")
        row = "".join(f"  {cells[fixture, patch.name]:>{col_width[fixture]}}" for fixture in fixtures)
        print(f"{label:{label_width}}{row}")


if __name__ == "__main__":
    main()
