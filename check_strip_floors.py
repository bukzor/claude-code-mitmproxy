#!/usr/bin/env python3
"""Verify no body we have actually seen strips less than its shape's floor.

`syspatch.strip_floors` calibrates the `_strip-rate` tripwire on the core of
each shape's newest fixture, so the floor should sit below what the sparsest
real session strips. Two things can push it back above: a promoted fixture
whose extra prose is real (fine, the floor should rise), or a session-optional
block that `blocks.d/` doesn't rule yet -- that block survives into the core,
inflates the floor, and every session without it captures a bogus
`low-strip-{shape}` incident. Nothing in production distinguishes that from
real drift, which is the point of checking here: run it after promoting a
fixture or editing `blocks.d/`.

Reads `log/prompt-captures/` (gitignored, so this needs a machine that has
been capturing), top level only -- `subagents/` bodies are never patched.
"""
from __future__ import annotations

from pathlib import Path

import shapes
import syspatch
import templates

CAPTURES_DIR = Path("log/prompt-captures")


def main():
    patches = templates.load_rules(syspatch.PATCHES_DIR)
    floors = syspatch.strip_floors(patches)

    # Same suppression as strip_floors: measuring is not triaging, and a
    # capture old enough to miss a patch is expected, not a regression.
    strips: dict[str, list[tuple[int, str]]] = {}
    for path in sorted(CAPTURES_DIR.glob("*.raw.md")):
        text = path.read_text()
        patched, _misses = templates.apply_rules(text, patches)
        strips.setdefault(shapes.shape_of(text), []).append(
            (len(text) - len(patched), path.name)
        )

    below = []
    for shape, floor in sorted(floors.items()):
        seen = sorted(strips.get(shape, []))
        witness = f"{seen[0][0]:5d}  {seen[0][1]}" if seen else "    -  (no capture)"
        print(f"{shape:14} floor={floor:5d}  sparsest={witness}")
        below += [(shape, floor, *s) for s in seen if s[0] < floor]

    assert not below, (
        below,
        "these captures strip less than their shape's floor, so sessions like "
        "them capture a bogus low-strip incident: either blocks.d/ is missing a "
        "block the fixture carries, or the fixture is not that shape's newest",
    )
    print(f"\n{sum(len(s) for s in strips.values())} captures, all above floor")


if __name__ == "__main__":
    main()
