#!/usr/bin/env python3
"""Per-patch match matrix across captured fixtures: which patches' match
templates hit which capture. Match misses are silent by design, so a patch
newly dark on a shape it used to hit is drift the loud path can't see —
run this whenever a new capture is promoted (see
design/040-design.kb/loudness-policy.md)."""
from __future__ import annotations

import sys
from pathlib import Path

from syspatch import PATCHES_DIR, _first_hit, load_patches

KB_DIR = Path("system-prompts.kb")


def main():
    fixtures = [Path(arg) for arg in sys.argv[1:]] or sorted(
        p for p in KB_DIR.iterdir() if p.suffix == ".md" and p.name != "CLAUDE.md"
    )
    texts = {fixture: fixture.read_text() for fixture in fixtures}
    patches = load_patches(PATCHES_DIR)
    assert patches, PATCHES_DIR

    label_width = max(len(p.name) for p in patches) + len(" (sunset)")
    print(" " * label_width + "".join(f"  {f.stem}" for f in fixtures))
    for patch in patches:
        label = patch.name + (" (sunset)" if patch.upstream_removed else "")
        row = "".join(
            f"  {'HIT' if _first_hit(texts[f], patch.matches) else '-':>{len(f.stem)}}"
            for f in fixtures
        )
        print(f"{label:{label_width}}{row}")


if __name__ == "__main__":
    main()
