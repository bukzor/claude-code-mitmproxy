#!/usr/bin/env python3
"""Print a captured system prompt as the live patch set would rewrite it.

The eyeball half of patch validation: diff two runs of this to see what a patch
edit really did, or read one to see what a session actually receives. Whether
the patches still *apply* is the check next door, `check_patches.py`, which is
why this one asserts nothing and always exits 0.

Usage: render_patched.py [SYSTEM.md [PATCHES_DIR]] -- defaults to the newest
full fixture and the live patch directory. Patched text to stdout, sizes to
stderr, so `render_patched.py > patched.md` is the file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import corpus
import syspatch
import templates


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    system_file = Path(argv[0]) if argv else corpus.latest_fixture()
    patches_dir = Path(argv[1]) if len(argv) > 1 else syspatch.PATCHES_DIR

    assert system_file.exists(), system_file
    text = system_file.read_text()
    patches = templates.load_rules(patches_dir)
    # The real pipeline, not `apply_rules`: this is what a session receives.
    # capture_dir=None keeps a hand-run from filing an incident nobody hit.
    result = syspatch.apply_patches(text, patches, capture_dir=None)

    print(f"original: {len(text)} chars", file=sys.stderr)
    print(f"patched:  {len(result)} chars", file=sys.stderr)
    print(f"delta:    {len(result) - len(text):+d} chars", file=sys.stderr)

    sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
