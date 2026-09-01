"""`survey_captures --promote`: the promotion duty, minus the human.

Every part of a fixture's name is readable off the capture it came from, so
promoting is a derivation rather than a decision. These tests pin the
derivation, because the failure they guard against is silent: a name that
disagrees with what the checks glob for produces a fixture nothing reads.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_mitmproxy import survey_captures


def drift(shape, version="2.1.257.c00", raw="cad91c751e18", text="a body\n", tmp_path=None):
    """A Drift over a capture the test writes, since promote() reads the raw."""
    path = (tmp_path or Path("/captures")) / f"v{version}_claude-fable-5_{raw}.raw.md"
    if tmp_path is not None:
        path.write_text(text)
    capture = survey_captures.Capture(version, "claude-fable-5", raw, path)
    return survey_captures.Drift(shape, "core8", version, len(text), capture, capture)


def test_name_carries_release_shape_and_raw_digest():
    assert survey_captures.fixture_name(drift("harness-opus")) == "v2.1.257-opus-cad91c75.md"


def test_the_default_shape_takes_no_shape_segment():
    assert survey_captures.fixture_name(drift("long-form")) == "v2.1.257-cad91c75.md"


def test_the_build_tag_is_not_part_of_the_name():
    """Fixtures are named by release: the build tag is a hash, and two of them
    at one release are the same fixture slot, not two."""
    name = survey_captures.fixture_name(drift("harness", version="2.1.257.f0d"))
    assert name == "v2.1.257-harness-cad91c75.md", name


def test_promote_writes_the_raw_body_verbatim(tmp_path):
    """The raw, not the masked sibling: `check_patches` needs pristine text so
    patch anchors see real content."""
    kb = tmp_path / "kb"
    kb.mkdir()
    captures = tmp_path / "captures"
    captures.mkdir()
    body = "You are an interactive agent\n"
    (done,) = survey_captures.promote(
        [drift("harness-opus", text=body, tmp_path=captures)], kb
    )
    written = kb / "v2.1.257-opus-cad91c75.md"
    assert written.read_text() == body, done
    assert "promoted" in done


def test_an_unknown_shape_is_left_for_a_human(tmp_path):
    """The one case with no derivable name -- and the one worth reading, since
    a body carrying no known marker is what a shape rename looks like."""
    kb = tmp_path / "kb"
    kb.mkdir()
    (done,) = survey_captures.promote([drift("?'# Something New'")], kb)
    assert "read it yourself" in done, done
    assert list(kb.iterdir()) == []


def test_promoting_over_an_existing_fixture_is_a_bug(tmp_path):
    """Same name means same raw body, which would already read as covered. If
    both are true at once, the drift predicate and the namer disagree."""
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "v2.1.257-opus-cad91c75.md").write_text("already here\n")
    with pytest.raises(AssertionError):
        survey_captures.promote([drift("harness-opus")], kb)
