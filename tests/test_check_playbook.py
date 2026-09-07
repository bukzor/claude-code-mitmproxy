"""`check_playbook`: the event taxonomy and `playbook.kb/` correspond -- one
entry per event type, named by the key a printed line starts with."""

from __future__ import annotations

import pytest

from claude_mitmproxy import check_playbook
from claude_mitmproxy import logging_handlers


def test_event_keys_walks_every_leaf_of_the_taxonomy():
    keys = logging_handlers.event_keys()
    assert {"capture.system-prompt", "incident.patch-miss", "promotion.over-budget"} <= keys, keys
    # Spelled as the files and the printed lines are, not as the attributes.
    assert all("_" not in key for key in keys), keys


@pytest.fixture
def playbook(tmp_path, monkeypatch):
    monkeypatch.setattr(check_playbook, "PLAYBOOK_DIR", tmp_path)
    (tmp_path / "CLAUDE.md").write_text("the guide is not an entry\n")
    return tmp_path


def test_every_type_wants_an_entry_and_every_entry_a_type(playbook):
    for key in logging_handlers.event_keys() - {"promotion.filed"}:
        (playbook / f"{key}.md").write_text("...\n")
    (playbook / "promotion.fled.md").write_text("a rename that left its entry behind\n")
    found = check_playbook.collect()
    assert check_playbook.types_without_an_entry(found) == ["promotion.filed"]
    assert check_playbook.entries_without_a_type(found) == ["promotion.fled"]


def test_a_complete_playbook_is_healthy(playbook):
    for key in logging_handlers.event_keys():
        (playbook / f"{key}.md").write_text("...\n")
    found = check_playbook.collect()
    assert not any(predicate(found) for predicate in check_playbook.PREDICATES)
