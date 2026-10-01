"""The trailing-newline convention holds only if nothing bypasses `textfile`.

Source-level, in the form `addons/reload.py` uses for its own invariants: a
bare `Path.read_text`/`write_text` anywhere in the library is a file whose
terminator now carries meaning again. There is no escape list, because none of
the library's text I/O is exempt -- a JSON or TOML parser is indifferent to the
stripped terminator, so routing it through `textfile` costs nothing. Byte and
fd access (`binpatch`, `flocked_logs`, `compress_traffic`) never named these
methods.
"""

from __future__ import annotations

import re

from claude_mitmproxy import repo_paths

BYPASS = re.compile(r"\.(read_text|write_text)\(")
LIBRARY = repo_paths.ROOT / "lib" / "claude_mitmproxy"


def bypasses(source: str) -> list[str]:
    return [line.strip() for line in source.splitlines() if BYPASS.search(line)]


def test_detector_sees_a_bypass():
    assert bypasses("x = path.read_text()\ny = 1\npath.write_text(y)\n") == [
        "x = path.read_text()",
        "path.write_text(y)",
    ]
    assert bypasses("textfile.read(path)\ntextfile.write(path, y)\n") == []


def test_library_reads_and_writes_text_only_through_textfile():
    found = {
        str(path.relative_to(LIBRARY)): hits
        for path in sorted(LIBRARY.rglob("*.py"))
        if path.name != "textfile.py"
        if (hits := bypasses(path.read_text()))
    }
    assert found == {}, found
