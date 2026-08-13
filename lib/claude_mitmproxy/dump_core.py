#!/usr/bin/env python3
"""Write each named body's *core* to stdout: masked (`masks.d/`), then with
the session-optional blocks (`blocks.d/`) deleted. This is the text whose
digest `survey_captures.py` prints in the `core` column, so it is what to
diff by hand when two captures unexpectedly share a core -- or unexpectedly
don't.

Usage: dump_core.py BODY.md ...
"""

from __future__ import annotations

import sys
from pathlib import Path

from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    assert argv, "usage: dump_core.py BODY.md ..."
    blocks = rule_templates.load_templates(prompt_patches.BLOCKS_DIR)
    for arg in argv:
        masked = incidents.normalize_body(Path(arg).read_text())
        core, _present = rule_templates.strip_blocks(masked, blocks)
        sys.stdout.write(core)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
