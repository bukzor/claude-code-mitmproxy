#!/usr/bin/env python3
"""Verify tool-description patches apply cleanly to their own upstream.md
fixtures -- the same texts the live proxy compares against, so a clean run
here means a drift-free session patches silently."""
from __future__ import annotations

import sys
from pathlib import Path

from toolpatch import PATCHES_DIR, apply_tool_patches, load_tool_patches


def main():
    patches_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else PATCHES_DIR
    patches = load_tool_patches(patches_dir)
    assert patches, ("no tool patches in", patches_dir)

    for patch in patches.values():
        for upstream in patch.upstreams:
            tools = [{"name": patch.name, "description": upstream, "input_schema": {}}]
            apply_tool_patches(tools, patches, capture_dir=None)
            assert tools[0]["description"] == patch.replacement, patch.name
            print(
                f"{patch.name}: {len(upstream)} -> {len(patch.replacement)} chars",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
