"""The on-disk convention: a text file is its content plus one terminator."""

from __future__ import annotations

import pytest

from claude_mitmproxy import textfile


@pytest.mark.parametrize(
    "content", ["", "a", "a\n", "a\n\n", "\n", "\n\n\n", "a\nb", "line\n\ntail\n"]
)
def test_round_trip_is_byte_exact(tmp_path, content):
    """Strip-one / append-one is a bijection, so no content is lost or gained
    -- including content that itself ends in blank lines."""
    path = tmp_path / "f.md"
    textfile.write(path, content)
    assert textfile.read(path) == content


def test_write_appends_exactly_one_newline(tmp_path):
    path = tmp_path / "f.md"
    textfile.write(path, "a\n")
    assert path.read_bytes() == b"a\n\n"


def test_read_strips_exactly_one_newline(tmp_path):
    path = tmp_path / "f.md"
    path.write_bytes(b"a\n\n\n")
    assert textfile.read(path) == "a\n\n"


def test_file_with_and_without_terminator_read_alike(tmp_path):
    """The point of the convention: an editor that adds or drops the final
    newline cannot change what a file means."""
    with_nl, without = tmp_path / "w.md", tmp_path / "wo.md"
    with_nl.write_bytes(b"text\n")
    without.write_bytes(b"text")
    assert textfile.read(with_nl) == textfile.read(without) == "text"


def test_empty_and_lone_newline_files_both_read_empty(tmp_path):
    """A blank `replace.md` is a deletion however an end-of-file fixer left it."""
    empty, lone = tmp_path / "e.md", tmp_path / "l.md"
    empty.write_bytes(b"")
    lone.write_bytes(b"\n")
    assert textfile.read(empty) == textfile.read(lone) == ""
