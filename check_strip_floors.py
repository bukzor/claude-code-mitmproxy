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

Usage: check_strip_floors.py [--data-only]

Structure is `verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

from typing import NamedTuple

import corpus
import shapes
import syspatch
import templates
import verdict


class StripRates(NamedTuple):
    floors: dict[str, int]  # shape -> the tripwire the live proxy arms
    # shape -> (bytes the patch set took off, capture name), sparsest first
    strips: dict[str, list[tuple[int, str]]]


def collect() -> StripRates:
    patches = templates.load_rules(syspatch.PATCHES_DIR)
    strips: dict[str, list[tuple[int, str]]] = {}
    for path in corpus.captures():
        text = path.read_text()
        # Misses suppressed the same way `strip_floors` suppresses them:
        # measuring is not triaging, and a capture old enough to miss a patch
        # is expected, not a regression.
        patched, _misses = templates.apply_rules(text, patches)
        strips.setdefault(shapes.shape_of(text), []).append(
            (len(text) - len(patched), path.name)
        )
    return StripRates(syspatch.strip_floors(patches), {k: sorted(v) for k, v in strips.items()})


def render(rates: StripRates) -> str:
    out = []
    for shape, floor in sorted(rates.floors.items()):
        seen = rates.strips.get(shape, [])
        witness = f"{seen[0][0]:5d}  {seen[0][1]}" if seen else "    -  (no capture)"
        out.append(f"{shape:14} floor={floor:5d}  sparsest={witness}")
    out.append(f"\n{sum(len(s) for s in rates.strips.values())} captures")
    return "\n".join(out) + "\n"


def captures_below_floor(rates: StripRates) -> dict[str, list[str]]:
    """captures stripping less than their shape's floor. Sessions like them
    capture a bogus low-strip incident: either `blocks.d/` is missing a block
    the fixture carries, or the fixture is not that shape's newest."""
    return {
        shape: [f"{name} stripped {n} < {floor}" for n, name in rates.strips.get(shape, []) if n < floor]
        for shape, floor in sorted(rates.floors.items())
        if any(n < floor for n, _ in rates.strips.get(shape, []))
    }


PREDICATES = (captures_below_floor,)


def main(argv: list[str] | None = None) -> int:
    return verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
