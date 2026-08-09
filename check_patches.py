#!/usr/bin/env python3
"""Verify system prompt patches apply cleanly against a captured system.md."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from syspatch import apply_patches
from templates import load_rules

DEFAULT_PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()
KB_DIR = Path("system-prompts.kb")

# Full-body capture name; -scope partials (e.g. v2.1.128-doing-tasks.md) excluded.
CAPTURE_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)\.md$")


def latest_capture(kb_dir: Path) -> Path:
    """Highest-versioned full capture in kb_dir. Validating against the current
    prompt keeps upstream-removed assertions silent; older captures still trip
    them (their text predates removal), so default to the newest."""
    versioned = [
        (tuple(int(g) for g in m.groups()), p)
        for p in kb_dir.iterdir()
        if (m := CAPTURE_RE.match(p.name))
    ]
    assert versioned, ("no vMAJOR.MINOR.PATCH.md captures in", kb_dir)
    return max(versioned)[1]


def main():
    system_file = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_capture(KB_DIR)
    patches_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PATCHES_DIR

    assert system_file.exists(), system_file
    text = system_file.read_text()
    patches = load_rules(patches_dir)
    result = apply_patches(text, patches, capture_dir=None)

    delta = len(result) - len(text)
    print(f"original: {len(text)} chars", file=sys.stderr)
    print(f"patched:  {len(result)} chars", file=sys.stderr)
    print(f"delta:    {delta:+d} chars", file=sys.stderr)

    sys.stdout.write(result)


if __name__ == "__main__":
    main()
