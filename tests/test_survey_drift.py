"""`survey_captures --drift`: which prompt copies no fixture covers.

The plain table answers "what is on disk"; drift answers the standing
promotion duty, which is a different question about the same rows -- and the
one nothing else in the repo asks, since additive drift trips no tripwire.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_mitmproxy import survey_captures


def surveyed(version, model, raw, core, shape, size):
    """A Surveyed record with only the fields drift grouping reads."""
    capture = survey_captures.Capture(version, model, raw, Path(f"/captures/{raw}.raw.md"))
    return survey_captures.Surveyed(capture, "x" * size, core, "", shape, "")


def test_promoted_cores_are_not_drift():
    rows = [surveyed("2.1.251.aaa", "sonnet-5", "r1", "core1", "long-form", 100)]
    assert survey_captures.drifted(rows, {("long-form", "core1")}) == []


def test_unpromoted_core_is_drift():
    rows = [surveyed("2.1.251.aaa", "sonnet-5", "r1", "core1", "long-form", 100)]
    (drift,) = survey_captures.drifted(rows, set())
    assert drift.shape == "long-form", drift
    assert drift.core == "core1", drift


def test_same_core_across_versions_is_one_group():
    """A core is a prompt copy, not a capture: many captures of one copy are
    one promotion, and the span is how long upstream has been serving it --
    which the arrival order of the captures must not disturb."""
    rows = [
        surveyed("2.1.241.aaa", "fable-5", "r1", "core1", "harness-fable", 100),
        surveyed("2.1.250.bbb", "fable-5", "r2", "core1", "harness-fable", 300),
        surveyed("2.1.246.ccc", "fable-5", "r3", "core1", "harness-fable", 200),
    ]
    (drift,) = survey_captures.drifted(rows, set())
    assert drift.span == "2.1.241.aaa..2.1.250.bbb", drift


def test_candidate_is_the_fullest_raw_in_the_group():
    """`system-prompts.kb/CLAUDE.md` promotes the fullest raw of a shape --
    a sparser session's body is a subset, and patches need the anchors."""
    rows = [
        surveyed("2.1.251.aaa", "opus-5", "small", "core1", "harness-opus", 100),
        surveyed("2.1.251.bbb", "opus-5", "big", "core1", "harness-opus", 900),
    ]
    (drift,) = survey_captures.drifted(rows, set())
    assert drift.candidate.raw == "big", drift
    assert drift.size == 900, drift


def test_shapes_are_grouped_separately():
    rows = [
        surveyed("2.1.251.aaa", "opus-5", "r1", "shared", "harness-opus", 100),
        surveyed("2.1.251.bbb", "sonnet-5", "r2", "shared", "long-form", 100),
    ]
    assert len(survey_captures.drifted(rows, set())) == 2


def test_newest_shape_group_sorts_first():
    """The promotion decision is per shape and always about the newest copy,
    so it must not be buried under historical cores that were never promoted."""
    rows = [
        surveyed("2.1.201.aaa", "sonnet-5", "old", "core-old", "long-form", 100),
        surveyed("2.1.251.bbb", "sonnet-5", "new", "core-new", "long-form", 100),
    ]
    drifts = survey_captures.drifted(rows, set())
    assert [d.core for d in drifts] == ["core-new", "core-old"], drifts


def test_unknown_flag_is_refused():
    """An unrecognized flag used to be taken as a name substring, match no
    capture, and report "no uncovered prompt copies in 0 captures" -- a
    confident wrong answer. `--data-only` is the one that provokes it: a real
    convention, but of the `check_*` commands, and this is a tool."""
    with pytest.raises(AssertionError):
        survey_captures.parse_argv(["--data-only"])


def test_drift_flag_is_separated_from_filters():
    parsed = survey_captures.parse_argv(["--drift", "v2.1.251"])
    assert (parsed.drift, parsed.current, parsed.filters) == (True, False, ["v2.1.251"])
    parsed = survey_captures.parse_argv(["v2.1.251"])
    assert (parsed.drift, parsed.current, parsed.filters) == (False, False, ["v2.1.251"])


def test_current_flag_implies_drift():
    """`--current` narrows the drift table; asking for it without `--drift`
    can only mean the drift question."""
    parsed = survey_captures.parse_argv(["--current"])
    assert (parsed.drift, parsed.current, parsed.promote) == (True, True, False)


def test_promote_flag_implies_current():
    """Promoting answers the duty `--current` states, so it inherits its scope:
    the backlog is deliberately uncovered, and filing it is not this command
    quietly deciding that promotion tracks everything ever captured."""
    parsed = survey_captures.parse_argv(["--promote"])
    assert (parsed.drift, parsed.current, parsed.promote) == (True, True, True)


def test_release_drops_the_build_tag():
    capture = survey_captures.Capture("2.1.251.da4", "opus-5", "r", Path("/x"))
    assert capture.release == (2, 1, 251), capture


def test_current_drift_keeps_only_the_newest_release():
    rows = [
        surveyed("2.1.250.aaa", "fable-5", "old", "core-old", "harness-fable", 100),
        surveyed("2.1.251.bbb", "fable-5", "new", "core-new", "harness-fable", 100),
    ]
    drifts = survey_captures.drifted(rows, set())
    current = survey_captures.current_drift(drifts, [row.capture for row in rows])
    assert [drift.core for drift in current] == ["core-new"], current


def test_build_tag_never_decides_currency():
    """Build tags are hashes, so the highest-sorting tag is not the newest
    capture. A copy uncovered at a lower-sorting tag of the current release is
    still what upstream serves, and comparing whole version strings hides it."""
    rows = [
        surveyed("2.1.251.171", "fable-5", "uncovered", "core1", "harness-fable", 100),
        surveyed("2.1.251.da4", "opus-5", "covered", "core2", "harness-opus", 100),
    ]
    drifts = survey_captures.drifted(rows, {("harness-opus", "core2")})
    current = survey_captures.current_drift(drifts, [row.capture for row in rows])
    assert [drift.core for drift in current] == ["core1"], current


def test_current_drift_refuses_an_empty_capture_set():
    """Answering "is anything uncovered" from no captures is the confident
    wrong answer this tool exists not to give -- the same one an unrecognized
    flag used to produce, reachable again through a filter matching nothing."""
    with pytest.raises(AssertionError):
        survey_captures.current_drift([], [])


def test_covered_newest_release_leaves_nothing_current():
    """The predicate clears itself: promoting the newest release's copies is
    what makes it quiet again, so backlog alone must never keep it red."""
    rows = [
        surveyed("2.1.250.aaa", "fable-5", "old", "core-old", "harness-fable", 100),
        surveyed("2.1.251.bbb", "fable-5", "new", "core-new", "harness-fable", 100),
    ]
    drifts = survey_captures.drifted(rows, {("harness-fable", "core-new")})
    assert survey_captures.current_drift(drifts, [row.capture for row in rows]) == []
