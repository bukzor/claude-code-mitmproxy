"""The promotion pass: what `--promote` files, glances at, commits and says.

Every line it prints that asks something of a reader starts with the type of
the event it reports, which is the key into `playbook.kb/`. The glance it
still owes a reader is each fixture's diff against the fixture it most
resembles -- smallest diff, found exhaustively -- because a fixture that
differs from a sibling only in text a mask or block rule should have
neutralized is flawed deduplication, and the diff is how that shows.
"""

from __future__ import annotations

import subprocess
from datetime import date

import pytest

from claude_mitmproxy import logging_handlers
from claude_mitmproxy import survey_captures
from test_logging_handlers import messages
from test_promote import drift


@pytest.fixture
def events_root(tmp_path):
    logging_handlers.reinstall_log_handlers(tmp_path / "events", tmp_path / "incidents")
    yield tmp_path / "events"
    logging_handlers.uninstall_log_handlers()


@pytest.fixture
def repo(tmp_path):
    """A kb with two fixtures and a captures dir, as the pass would see them."""
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "v2.1.250-opus-aaaaaaaa.md").write_text("one\ntwo\nthree\nfour\n")
    (kb / "v2.1.240-bbbbbbbb.md").write_text("alpha\nbeta\ngamma\ndelta\n")
    captures = tmp_path / "captures"
    captures.mkdir()
    return kb, captures


def commit_ok(promoted):
    return survey_captures.CommitResult(0, "")


def commit_refused(promoted):
    return survey_captures.CommitResult(1, "check_strip_floors refused it\n1 failed in 2.31s\n")


def test_distance_counts_the_lines_that_differ():
    assert survey_captures.distance("a\nb\nc\n", "a\nb\nc\n") == 0
    assert survey_captures.distance("a\nb\nc\n", "a\nB\nc\n") == 2
    assert survey_captures.distance("a\nb\nc\n", "a\nb\nc\nd\n") == 1


def test_nearest_is_the_fixture_with_the_smallest_diff():
    others = {"far": "x\ny\nz\n", "near": "one\n", "nearer": "one\ntwo\nthree\nfour\n"}
    nearest = survey_captures.nearest_fixture("new", "one\ntwo\nthree\nfive\n", others)
    assert nearest.name == "nearer", nearest
    assert nearest.distance == 2, nearest
    assert nearest.compared == 3, nearest


def test_the_glance_is_the_diff_when_it_is_small():
    nearest = survey_captures.nearest_fixture("new", "one\ntwo\nthree\nfive\n", {"near": "one\ntwo\nthree\nfour\n"})
    text = survey_captures.glance(nearest, survey_captures.KB_DIR)
    assert "-four\n+five\n" in text, text


def test_a_large_diff_is_summarised_instead_of_printed(monkeypatch):
    monkeypatch.setattr(survey_captures, "GLANCE_LINES", 2)
    nearest = survey_captures.nearest_fixture("new", "a\nb\nc\nd\n", {"near": "w\nx\ny\nz\n"})
    text = survey_captures.glance(nearest, survey_captures.KB_DIR)
    assert text.startswith("diff of 8 lines not shown: diff "), text
    assert "+a" not in text


def test_a_fresh_promotion_is_a_filed_event_with_its_glance(repo, events_root, monkeypatch):
    kb, captures = repo
    monkeypatch.setattr(survey_captures, "commit_promotions", commit_ok)
    drifts = [drift("harness-opus", version="2.1.257.c00", text="one\ntwo\nthree\nfive\n", tmp_path=captures)]
    out = survey_captures.promotion_pass(drifts, kb)
    assert out.startswith(
        "promotion.filed v2.1.257-opus-cad91c75.md <- v2.1.257.c00_claude-fable-5_cad91c751e18.raw.md"
        " nearest=v2.1.250-opus-aaaaaaaa distance=2\n"
    ), out
    assert "-four\n+five\n" in out, out
    assert out.endswith("committed 1 fixture\n"), out
    (event,) = messages(events_root, "promotion/filed")
    assert event.startswith("v2.1.257-opus-cad91c75.md <- "), event
    assert " compared=2 seconds=" in event, event


def test_a_refused_commit_is_a_refused_event_and_keeps_the_glance(repo, events_root, monkeypatch):
    kb, captures = repo
    monkeypatch.setattr(survey_captures, "commit_promotions", commit_refused)
    drifts = [drift("harness-opus", text="one\ntwo\nthree\nfive\n", tmp_path=captures)]
    out = survey_captures.promotion_pass(drifts, kb)
    assert "promotion.filed v2.1.257-opus-cad91c75.md" in out, out
    assert "promotion.refused exit 1: v2.1.257-opus-cad91c75.md\n" in out, out
    assert "check_strip_floors refused it\n1 failed\n" in out, out
    assert "2.31s" not in out, out
    (event,) = messages(events_root, "promotion/refused")
    assert event == "exit 1: v2.1.257-opus-cad91c75.md", event


def test_a_retry_repeats_the_glance_but_not_the_filed_event(repo, events_root, monkeypatch):
    """The watch prints on change, so a refused promotion must read the same
    on every pass until it is fixed; the event file, though, records the
    filing once."""
    kb, captures = repo
    monkeypatch.setattr(survey_captures, "commit_promotions", commit_refused)
    drifts = [drift("harness-opus", text="one\ntwo\nthree\nfive\n", tmp_path=captures)]
    first = survey_captures.promotion_pass(drifts, kb)
    second = survey_captures.promotion_pass(drifts, kb)
    assert first == second
    assert len(messages(events_root, "promotion/filed")) == 1
    assert len(messages(events_root, "promotion/refused")) == 2


def test_a_declined_copy_is_a_declined_event(repo, events_root, monkeypatch):
    kb, captures = repo
    monkeypatch.setattr(survey_captures, "commit_promotions", commit_ok)
    out = survey_captures.promotion_pass([drift("?'# Something New'", tmp_path=captures)], kb)
    assert out.startswith("promotion.declined "), out
    assert "unknown shape ?'# Something New'" in out, out
    assert "committed" not in out
    assert len(messages(events_root, "promotion/declined")) == 1


def test_a_pass_over_budget_says_so(repo, events_root, monkeypatch):
    kb, captures = repo
    monkeypatch.setattr(survey_captures, "commit_promotions", commit_ok)
    monkeypatch.setattr(survey_captures, "DIFF_BUDGET_SECONDS", 0.0)
    drifts = [drift("harness-opus", text="one\ntwo\nthree\nfive\n", tmp_path=captures)]
    out = survey_captures.promotion_pass(drifts, kb)
    assert "\npromotion.over-budget compared=2 seconds=0 budget=0\n" in out, out
    (event,) = messages(events_root, "promotion/over-budget")
    assert event.startswith("compared=2 seconds="), event


def test_a_pass_within_budget_says_nothing_about_it(repo, events_root, monkeypatch):
    kb, captures = repo
    monkeypatch.setattr(survey_captures, "commit_promotions", commit_ok)
    drifts = [drift("harness-opus", text="one\ntwo\nthree\nfive\n", tmp_path=captures)]
    assert "over-budget" not in survey_captures.promotion_pass(drifts, kb)
    assert not (events_root / "promotion" / f"over-budget.{date.today():%Y-%m-%d}.log").exists()


def test_the_all_clear_carries_no_count():
    """A count changes when a covered capture arrives, and a watch that prints
    on change would then announce nothing as if it were something."""
    assert survey_captures.all_clear(current=True) == "no uncovered prompt copies at the newest release"
    assert survey_captures.all_clear(current=False) == "no uncovered prompt copies"


def test_coverage_is_read_from_what_is_committed(tmp_path):
    """A fixture a refused commit left on disk covers nothing yet, or its copy
    would stop drifting and the commit would never be retried."""
    kb = tmp_path / "system-prompts.kb"
    kb.mkdir()
    (kb / "v2.1.250-opus-aaaaaaaa.md").write_text("one\n")
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "--", "system-prompts.kb"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "one", "--", "system-prompts.kb"], check=True)
    (kb / "v2.1.257-opus-cccccccc.md").write_text("two\n")  # filed, refused, left behind
    assert survey_captures.read_fixtures(kb).keys() == {"v2.1.250-opus-aaaaaaaa", "v2.1.257-opus-cccccccc"}
    assert survey_captures.committed_fixtures(kb) == {"v2.1.250-opus-aaaaaaaa": "one\n"}


def test_event_key_is_the_type_below_the_events_root():
    assert logging_handlers.event_key(logging_handlers.events.promotion.filed) == "promotion.filed"
    assert logging_handlers.event_key(logging_handlers.events.incident.patch_miss) == "incident.patch-miss"
