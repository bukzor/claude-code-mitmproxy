"""The one way this repo reads and writes a text file.

Whether a file ends in a newline is too unreliable across editors, fixers and
tools to carry meaning, so it carries none: a file is its content plus exactly
one terminator. Reading strips one trailing newline if there is one; writing
appends one unconditionally. Strings in memory therefore have no terminator
except where trailing blank lines are themselves the content, and strings on
disk always have one that is not content.

Strip-one/append-one is a bijection -- a file ending in three newlines reads
as content ending in two, and writing that content restores it byte for byte
-- which `rstrip` would not give.

The convention governs files, not wire text: a body arriving from the network
keeps whatever trailing newline upstream sent, which is what the line
anchoring in `rule_templates` absorbs. `tests/test_textfile_enforced.py`
holds the rest of the repo to calling nothing else.
"""

from __future__ import annotations

from pathlib import Path


def read(path: Path) -> str:
    text = path.read_text()
    return text.removesuffix("\n")


def write(path: Path, text: str) -> None:
    path.write_text(text + "\n")
