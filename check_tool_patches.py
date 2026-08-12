#!/usr/bin/env python3
"""Tool-description patches against their own recorded upstreams -- the same
texts the live proxy compares against, so a clean run here means a drift-free
session patches silently.

Usage: check_tool_patches.py [--data-only]

Structure is `verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

from typing import NamedTuple

import toolpatch
import verdict


class Rewrite(NamedTuple):
    tool: str
    upstream: int  # chars of the description as upstream sends it
    replacement: int  # chars of what the proxy serves instead
    served: str  # what the patch set actually produced for this upstream


class ToolPatches(NamedTuple):
    rewrites: tuple[Rewrite, ...]
    replacements: dict[str, str]  # tool -> the one text every upstream must reach


def collect() -> ToolPatches:
    patches = toolpatch.load_tool_patches(toolpatch.PATCHES_DIR)
    rewrites = []
    for patch in patches.values():
        for upstream in patch.upstreams:
            tools = [{"name": patch.name, "description": upstream, "input_schema": {}}]
            # capture_dir=None: provoking a miss here must not file an incident
            # for someone to triage (`incidents.py` documents the seam).
            toolpatch.apply_tool_patches(tools, patches, capture_dir=None)
            rewrites.append(
                Rewrite(patch.name, len(upstream), len(patch.replacement), tools[0]["description"])
            )
    return ToolPatches(
        tuple(rewrites), {patch.name: patch.replacement for patch in patches.values()}
    )


def render(patched: ToolPatches) -> str:
    if not patched.rewrites:
        return f"no tool-description patches installed in {toolpatch.PATCHES_DIR}\n"
    out = [
        f"{r.tool:16} {r.upstream:6} -> {r.replacement:5} chars" for r in patched.rewrites
    ]
    out.append(f"\n{len(patched.replacements)} tools, {len(patched.rewrites)} recorded upstreams")
    return "\n".join(out) + "\n"


def upstreams_that_miss(patched: ToolPatches) -> dict[str, list[str]]:
    """recorded upstreams that no longer reach their patch's replacement.
    Upstreams accumulate rather than replace, so every drifted description
    stays here as its own case: one that stops arriving at the replacement
    means the patch that claimed it no longer recognizes it."""
    missed: dict[str, list[str]] = {}
    for rewrite in patched.rewrites:
        if rewrite.served != patched.replacements[rewrite.tool]:
            missed.setdefault(rewrite.tool, []).append(f"{rewrite.upstream} chars unpatched")
    return missed


PREDICATES = (upstreams_that_miss,)


def main(argv: list[str] | None = None) -> int:
    return verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
