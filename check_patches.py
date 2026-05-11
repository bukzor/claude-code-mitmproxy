#!/usr/bin/env python3
"""Verify system prompt patches apply cleanly against a captured system.md."""
from __future__ import annotations

import sys
from pathlib import Path

from syspatch import apply_patches, load_patches

DEFAULT_PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()


def main():
    system_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("system-prompts.kb/v2.1.76.md")
    patches_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PATCHES_DIR

    assert system_file.exists(), system_file
    text = system_file.read_text()
    patches = load_patches(patches_dir)
    result = apply_patches(text, patches)

    delta = len(result) - len(text)
    print(f"original: {len(text)} chars", file=sys.stderr)
    print(f"patched:  {len(result)} chars", file=sys.stderr)
    print(f"delta:    {delta:+d} chars", file=sys.stderr)

    sys.stdout.write(result)


if __name__ == "__main__":
    main()
