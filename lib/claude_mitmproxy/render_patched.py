#!/usr/bin/env python3
"""Print a captured system prompt as the live patch set would rewrite it.

The eyeball half of patch validation: diff two runs of this to see what a patch
edit really did, or read one to see what a session actually receives. Whether
the patches still *apply* is the check next door, `check_patches.py`, which is
why this one asserts nothing and always exits 0.

Usage: render_patched.py [SYSTEM.md [PATCHES_DIR]] -- defaults to the live
patch directory and the first of the current release's full fixtures, naming
it on stderr because there is usually more than one and this prints a
document, not a survey. Patched text to stdout, sizes to stderr, so
`render_patched.py > patched.md` is the file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from claude_mitmproxy import prompt_corpus
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    current = prompt_corpus.current_fixtures()
    system_file = Path(argv[0]) if argv else current[0]
    patches_dir = Path(argv[1]) if len(argv) > 1 else prompt_patches.PATCHES_DIR

    assert system_file.exists(), system_file
    text = system_file.read_text()
    patches = rule_templates.load_rules(patches_dir)
    # The real pipeline, not `apply_rules`: this is what a session receives.
    # capture_dir=None keeps a hand-run from filing an incident nobody hit.
    result = prompt_patches.apply_patches(text, patches, capture_dir=None)

    print(f"source:   {system_file.stem} (of {len(current)} current)", file=sys.stderr)
    print(f"original: {len(text)} chars", file=sys.stderr)
    print(f"patched:  {len(result)} chars", file=sys.stderr)
    print(f"delta:    {len(result) - len(text):+d} chars", file=sys.stderr)

    sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
