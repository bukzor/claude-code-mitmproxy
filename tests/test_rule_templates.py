"""What a template file means, independent of how it ends.

Every rule file is read through `textfile`, so a file with and without its
terminator is the same template; a deletion then takes the line's own
terminator with it, which is what lets the terminator be absent from the
template at all.
"""

from __future__ import annotations

import pytest

from claude_mitmproxy import rule_templates

BODIES = ["x\nA\ny", "A\ny", "x\nA", "A", "x\nA\n", "A\n"]


def write_rule(directory, match: bytes, replace: bytes):
    rule = directory / "rule"
    rule.mkdir(parents=True)
    (rule / "match.md").write_bytes(match)
    (rule / "replace.md").write_bytes(replace)
    return rule_templates.load_rules(directory)


@pytest.mark.parametrize("terminator", [b"", b"\n"])
@pytest.mark.parametrize(
    "body, expected",
    [
        ("x\nA\ny", "x\ny"),
        ("A\ny", "y"),
        ("x\nA", "x"),
        ("A", ""),
        ("x\nA\n", "x\n"),
        ("A\n", ""),
    ],
)
def test_deletion_takes_the_line_and_its_terminator(tmp_path, terminator, body, expected):
    rules = write_rule(tmp_path, b"A" + terminator, b"")
    patched, misses = rule_templates.apply_rules(body, rules)
    assert (patched, misses) == (expected, [])


@pytest.mark.parametrize("terminator", [b"", b"\n"])
def test_replacement_keeps_the_bodys_own_terminator(tmp_path, terminator):
    rules = write_rule(tmp_path, b"A" + terminator, b"B" + terminator)
    assert rule_templates.apply_rules("x\nA\ny", rules)[0] == "x\nB\ny"
    assert rule_templates.apply_rules("x\nA", rules)[0] == "x\nB"
    assert rule_templates.apply_rules("x\nA\n", rules)[0] == "x\nB\n"


def test_lone_newline_replace_is_a_deletion(tmp_path):
    """An end-of-file fixer turning an empty `replace.md` into one newline must
    not turn the deletion into a blank-line insertion."""
    rules = write_rule(tmp_path, b"A\n", b"\n")
    assert rule_templates.apply_rules("x\nA\ny", rules)[0] == "x\ny"


def test_trailing_blank_line_is_content(tmp_path):
    """Two terminators on disk is one blank line of template: it matches the
    line and the empty line after it, and only there."""
    rules = write_rule(tmp_path, b"A\n\n", b"")
    assert rule_templates.apply_rules("x\nA\n\ny", rules)[0] == "x\ny"
    assert rule_templates.apply_rules("x\nA\ny", rules)[0] == "x\nA\ny"


def test_blocks_are_deleted_with_their_terminator(tmp_path):
    (tmp_path / "block.md").write_bytes(b"A\n")
    blocks = rule_templates.load_templates(tmp_path)
    assert rule_templates.strip_blocks("x\nA\ny\nA", blocks) == ("x\ny", ["block"])


def test_cutting_trailing_lines_is_joining_the_rest(tmp_path):
    """Two rules deleting adjacent last lines: whichever the order, what is
    left is the remaining lines joined, with no stray break at the end."""
    for name in ("a", "b"):
        (tmp_path / f"{name}.md").write_bytes(name.upper().encode() + b"\n")
    blocks = rule_templates.load_templates(tmp_path)
    assert rule_templates.strip_blocks("x\nA\nB", blocks)[0] == "x"
    assert rule_templates.strip_blocks("x\nB\nA", blocks)[0] == "x"
    assert rule_templates.strip_blocks("A\nB", blocks)[0] == ""


def test_mask_leaves_the_terminator_alone(tmp_path):
    (tmp_path / "mask.md").write_bytes(b"cwd: $CWD\n")
    masks = rule_templates.load_templates(tmp_path)
    masked = rule_templates.apply_masks("cwd: /a\nnext\ncwd: /b", masks)
    assert masked == "cwd: $CWD\nnext\ncwd: $CWD"
    assert rule_templates.apply_masks(masked, masks) == masked
