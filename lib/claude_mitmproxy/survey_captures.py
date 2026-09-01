#!/usr/bin/env python3
"""Inventory of captured system-prompt bodies: one row per raw capture in
log/prompt-captures/, classified by prompt shape, with the session-optional
blocks it carries and whether its exact body is already promoted into
system-prompts.kb/. This serves the standing promotion duty ("check for
cc_versions newer than the newest full-body capture") -- promotion has no
automatic trigger, so this table is the "someone looks" step.

`--drift` answers the duty directly instead of leaving it to the eye: one row
per prompt copy (shape + core digest) that no fixture covers, newest first,
naming the raw to promote. The plain table is still the way to read what is on
disk; at ~100 captures it is not the way to spot what is missing.

`--current` narrows that to the copies carried at the newest release -- the
predicate that earns an interruption, and so the one `driftwatch.sh` polls.
Everything it drops is backlog, which is why the full drift table is the wrong
thing to wire a signal to.

`--promote` answers it instead of printing it: every current row copied into
`system-prompts.kb/` under a name derived from the capture. Nothing is chosen,
so nothing is left for a reader to decide -- see `promote` for why what
remained of this duty was toil.

Usage: survey_captures.py [--drift] [--current] [--promote] [SUBSTRING ...]
Rows are filtered to filenames containing any SUBSTRING (e.g. "2.1.221").
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_shape
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates

CAPTURES_DIR = Path("log/prompt-captures")
KB_DIR = Path("system-prompts.kb")


class Capture(NamedTuple):
    version: str  # cc_version incl. build tag, e.g. "2.1.221.b87"
    model: str
    raw: str  # digest of the body as sent -- the capture's identity and name
    path: Path

    @property
    def release(self) -> tuple[int, ...]:
        """The numeric version, build tag dropped.

        Build tags are hashes, so ordering two of them is noise -- only the
        release orders. Keeping them apart is what lets `current_drift` ask
        whether upstream is serving a copy now instead of whether its capture
        happened to carry the highest-sorting tag."""
        release, _, _ = self.version.rpartition(".")
        return tuple(int(part) for part in release.split("."))

    @property
    def sort_key(self) -> tuple:
        _, _, build = self.version.rpartition(".")
        return self.release + (build, self.model)


def parse_name(path: Path) -> Capture:
    stem = path.name.removesuffix(".raw.md")
    version, model, raw = stem.rsplit("_", 2)
    assert version.startswith("v"), path
    return Capture(version.removeprefix("v"), model, raw, path)


def core_of(text: str, blocks: tuple[rule_templates.Template, ...]) -> tuple[str, str]:
    """The capture's (core digest, session-optional blocks it carries).

    The core digest is what's left once every block this session happened to
    switch on is deleted: two captures share it exactly when they carry the
    same prompt copy, whatever their sessions differed on. Blocks are stripped
    from the masked body, so a block template can be written against the
    tokens masks leave behind instead of the volatile text they replaced."""
    stripped, present = rule_templates.strip_blocks(incidents.normalize_body(text), blocks)
    return incidents.digest_of(stripped), ",".join(present)


def promoted_as(text: str, kb_texts: dict[str, str]) -> str:
    return next((name for name, kb in kb_texts.items() if kb == text), "")


class Surveyed(NamedTuple):
    """One capture, with everything the two views derive from it."""

    capture: Capture
    text: str
    core: str
    blocks: str
    shape: str
    promoted: str


class Drift(NamedTuple):
    """One prompt copy no fixture covers, and the raw that would cover it."""

    shape: str
    core: str
    span: str
    size: int
    candidate: Capture
    newest: Capture  # latest capture of this copy -- what dates it


def survey(
    captures: list[Capture], kb_texts: dict[str, str], blocks: tuple[rule_templates.Template, ...]
) -> list[Surveyed]:
    rows = []
    for capture in sorted(captures, key=lambda c: c.sort_key):
        text = capture.path.read_text()
        core, present = core_of(text, blocks)
        rows.append(
            Surveyed(
                capture,
                text,
                core,
                present,
                prompt_shape.shape_of(text),
                promoted_as(text, kb_texts),
            )
        )
    return rows


def promoted_cores(
    kb_texts: dict[str, str], blocks: tuple[rule_templates.Template, ...]
) -> set[tuple[str, str]]:
    """The (shape, core) pairs the fixtures already cover.

    Taken from the fixtures themselves rather than from whichever captures
    happen to equal one: a fixture outlives the capture it was promoted from,
    and reading it off the captures would call its copy uncovered once the
    capture is gone."""
    return {
        (prompt_shape.shape_of(text), core_of(text, blocks)[0])
        for text in kb_texts.values()
    }


def drifted(rows: list[Surveyed], covered: set[tuple[str, str]]) -> list[Drift]:
    """Uncovered prompt copies, newest first within each shape.

    Grouped by (shape, core) because the promotion decision is per copy, not
    per capture: a hundred captures of one copy need one fixture. Old
    uncovered copies stay listed -- they are the context that says whether the
    newest one is a fresh rewrite or the latest of a drifting series -- but
    they sort below it, since only the newest is a duty."""
    groups: dict[tuple[str, str], list[Surveyed]] = {}
    for row in rows:
        key = (row.shape, row.core)
        if key not in covered:
            groups.setdefault(key, []).append(row)

    dated = []
    for (shape, core), members in groups.items():
        by_age = sorted(members, key=lambda r: r.capture.sort_key)
        fullest = max(members, key=lambda r: len(r.text))
        oldest, newest = by_age[0].capture, by_age[-1].capture
        dated.append((
            newest.sort_key,
            Drift(
                shape=shape,
                core=core,
                span=(
                    oldest.version
                    if oldest.version == newest.version
                    else f"{oldest.version}..{newest.version}"
                ),
                size=len(fullest.text),
                candidate=fullest.capture,
                newest=newest,
            ),
        ))

    # Two passes, leaning on a stable sort: recency descending first, then
    # shape ascending, which preserves it within each shape. One pass can't
    # do it -- sort_key mixes ints and strings, so it has no negation.
    dated.sort(key=lambda pair: pair[0], reverse=True)
    dated.sort(key=lambda pair: pair[1].shape)
    return [drift for _, drift in dated]


def current_drift(drifts: list[Drift], captures: list[Capture]) -> list[Drift]:
    """The uncovered copies upstream is serving now -- the ones that earn an
    interruption (`design/040-design.kb/every-duty-has-an-occasion.md`).

    The rest of the drift table is backlog: real, but no evidence anything
    moved, and a signal that fires on it is red forever. Newest release across
    every shape rather than per shape, since a shape absent from newer releases
    is one upstream stopped serving."""
    assert captures, "no captures to date: 'nothing uncovered' would be vacuous"
    newest = max(capture.release for capture in captures)
    return [drift for drift in drifts if drift.newest.release == newest]


def fixture_name(drift: Drift) -> str:
    """What a copy is promoted *as* -- derived, never chosen.

    Release, shape and raw digest are all readable off the capture, so two
    promoters agree and neither has to know which copy arrived first. The raw
    digest rather than the core: core digests move whenever `blocks.d/`
    changes, and a name a rule edit can invalidate is what
    `design/040-design.kb/content-addressed-capture.md` forbids.
    """
    release = ".".join(str(part) for part in drift.candidate.release)
    suffix = prompt_shape.FIXTURE_SUFFIX[drift.shape]
    return f"v{release}{suffix}-{drift.candidate.raw[:8]}.md"


def promote(drifts: list[Drift], kb_dir: Path) -> list[str]:
    """Copy each uncovered copy's raw body into the fixture collection.

    Nothing here decides anything, which is the point. Since "promote every
    one of them" there is no winner to pick, and with `check_patches` reading
    every fixture at the newest release there is no privileged name to award
    either -- so what was left of this duty was a human performing a `cp` that
    a function can derive. A duty with no decision in it is toil, and
    `design/040-design.kb/every-duty-has-an-occasion.md` says to bind that to
    its occasion rather than report it. The occasion is the commit that
    follows: touching `system-prompts.kb/` runs the whole offline suite.

    A shape this repo has no marker for is the exception, and it stays a
    human's: it has no derivable name, and a body carrying no known marker is
    the one drift worth reading rather than filing.
    """
    done = []
    for drift in drifts:
        if drift.shape not in prompt_shape.FIXTURE_SUFFIX:
            done.append(f"unknown shape {drift.shape}, read it yourself: {drift.candidate.path}")
            continue
        target = kb_dir / fixture_name(drift)
        assert not target.exists(), (target, "already promoted, yet its copy reads as uncovered")
        target.write_text(drift.candidate.path.read_text())
        done.append(f"promoted {drift.candidate.path} -> {target}")
    return done


def inventory_table(rows: list[Surveyed]) -> list[tuple[str, ...]]:
    header = ("version", "model", "raw", "core", "bytes", "shape", "promoted", "blocks")
    return [header] + [
        (
            row.capture.version,
            row.capture.model.removeprefix("claude-"),
            row.capture.raw,
            row.core,
            str(len(row.text)),
            row.shape,
            row.promoted,
            row.blocks,
        )
        for row in rows
    ]


def drift_table(drifts: list[Drift]) -> list[tuple[str, ...]]:
    header = ("shape", "core", "versions", "bytes", "promote")
    return [header] + [
        (
            drift.shape,
            drift.core,
            drift.span,
            str(drift.size),
            str(drift.candidate.path),
        )
        for drift in drifts
    ]


def trailer(count: int, current: bool) -> str:
    """What the reader should do with the table above."""
    if current:
        return (
            f"{count} uncovered at the newest release: upstream is serving prompt"
            " text no fixture covers, so every patch verified against a fixture is"
            " unverified against what ships. `--promote` files every row and"
            " names it; copies of one shape coexist while upstream reworks it,"
            " and covering all of them is what makes this quiet."
        )
    else:
        return (
            f"{count} uncovered copies."
            " Only the newest release is a duty (`--current`); the rest is backlog,"
            " left uncovered because promotion tracks what upstream serves now."
        )


def render(rows: list[tuple[str, ...]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "".join(
        "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() + "\n"
        for row in rows
    )


class Args(NamedTuple):
    drift: bool
    current: bool
    promote: bool
    filters: list[str]


FLAGS = ("--drift", "--current", "--promote")


def parse_argv(argv: list[str]) -> Args:
    """The two flags, plus name substrings to narrow the captures.

    An unrecognized flag is refused rather than taken as a filter. `--data-only`
    is the one that provokes it -- a real convention, but of the `check_*`
    commands, and this is a tool with no verdict to suppress -- and as a filter
    it matched no capture and reported "no uncovered prompt copies in 0
    captures": a confident, wrong, and entirely silent answer to the one
    question this tool exists to ask."""
    filters = [arg for arg in argv if arg not in FLAGS]
    unknown = [arg for arg in filters if arg.startswith("-")]
    assert not unknown, (unknown, "unknown flag; other arguments are name substrings")
    promote = "--promote" in argv
    current = "--current" in argv or promote
    return Args("--drift" in argv or current, current, promote, filters)


def main() -> None:
    args = parse_argv(sys.argv[1:])
    raws = sorted(CAPTURES_DIR.glob("*.raw.md"))
    assert raws, CAPTURES_DIR
    captures = [
        parse_name(path)
        for path in raws
        if not args.filters or any(f in path.name for f in args.filters)
    ]
    assert captures, (args.filters, "matched no capture; every answer below would be vacuous")
    kb_texts = {
        p.stem: p.read_text()
        for p in sorted(KB_DIR.iterdir())
        if p.suffix == ".md" and p.name != "CLAUDE.md"
    }

    blocks = rule_templates.load_templates(prompt_patches.BLOCKS_DIR)
    rows = survey(captures, kb_texts, blocks)

    if args.drift:
        drifts = drifted(rows, promoted_cores(kb_texts, blocks))
        scope = ""
        if args.current:
            drifts = current_drift(drifts, captures)
            scope = " at the newest release"
        if not drifts:
            print(f"no uncovered prompt copies{scope} in {len(rows)} captures")
        elif args.promote:
            print("\n".join(promote(drifts, KB_DIR)))
        else:
            sys.stdout.write(render(drift_table(drifts)))
            print("\n" + trailer(len(drifts), args.current))
    else:
        sys.stdout.write(render(inventory_table(rows)))


if __name__ == "__main__":
    main()
