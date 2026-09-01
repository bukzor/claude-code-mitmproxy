"""`prompt_corpus.current_fixtures`: which bodies a patch check must satisfy.

Upstream serves several bodies at one release -- a shape per model, and copies
of one shape while it reworks the text -- so "the current prompt" is a set. The
selection is what decides whether a green `check_patches` means the patch set
lands on everything shipping, or only on whichever file sorted first.
"""

from __future__ import annotations

import pytest

from claude_mitmproxy import prompt_corpus
from claude_mitmproxy import prompt_location
from claude_mitmproxy import prompt_patches

FULL = f"{prompt_location.BODY_MARKER}\nYou are Claude Code.\n"
PARTIAL = "# Doing tasks\n\nOne section, no body marker.\n"


@pytest.fixture
def kb(tmp_path, monkeypatch):
    """A fixture directory the test writes, standing in for the real one."""
    monkeypatch.setattr(prompt_patches, "KB_DIR", tmp_path)
    return tmp_path


def promote(kb, name, text=FULL):
    (kb / name).write_text(text)


def test_every_copy_at_the_newest_release(kb):
    promote(kb, "v2.1.256.md")
    promote(kb, "v2.1.257-opus.md")
    promote(kb, "v2.1.257-92b0bb81.md")
    assert [p.name for p in prompt_corpus.current_fixtures()] == [
        "v2.1.257-92b0bb81.md",
        "v2.1.257-opus.md",
    ]


def test_release_ordering_is_numeric_not_lexical(kb):
    promote(kb, "v2.1.9.md")
    promote(kb, "v2.1.10.md")
    assert [p.name for p in prompt_corpus.current_fixtures()] == ["v2.1.10.md"]


def test_scope_partials_are_not_current(kb):
    """A partial carries one section, so patches anchored outside it miss for a
    reason that is not drift. The filename cannot say that -- `-doing-tasks`
    and `-opus` are the same shape of suffix -- so the body is asked."""
    promote(kb, "v2.1.257.md")
    promote(kb, "v2.1.257-doing-tasks.md", PARTIAL)
    assert [p.name for p in prompt_corpus.current_fixtures()] == ["v2.1.257.md"]


def test_a_partial_does_not_set_the_release(kb):
    """The newest *full* body decides, not the newest file: a partial promoted
    above the fixtures would otherwise elect itself and check nothing."""
    promote(kb, "v2.1.257.md")
    promote(kb, "v2.1.258-doing-tasks.md", PARTIAL)
    assert [p.name for p in prompt_corpus.current_fixtures()] == ["v2.1.257.md"]


def test_no_full_fixture_is_an_error(kb):
    """Empty is never "nothing to check": a wrong KB_DIR would otherwise make a
    check that examined no bodies at all report green."""
    promote(kb, "v2.1.257-doing-tasks.md", PARTIAL)
    with pytest.raises(AssertionError):
        prompt_corpus.current_fixtures()
