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

Usage: survey_captures.py [--drift] [SUBSTRING ...]
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
    def sort_key(self) -> tuple:
        release, _, build = self.version.rpartition(".")
        return tuple(int(part) for part in release.split(".")) + (build, self.model)


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
    seen: int  # captures carrying this copy -- 1 is a blip, many is a trend
    span: str
    size: int
    candidate: Capture


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
                seen=len(members),
                span=(
                    oldest.version
                    if oldest.version == newest.version
                    else f"{oldest.version}..{newest.version}"
                ),
                size=len(fullest.text),
                candidate=fullest.capture,
            ),
        ))

    # Two passes, leaning on a stable sort: recency descending first, then
    # shape ascending, which preserves it within each shape. One pass can't
    # do it -- sort_key mixes ints and strings, so it has no negation.
    dated.sort(key=lambda pair: pair[0], reverse=True)
    dated.sort(key=lambda pair: pair[1].shape)
    return [drift for _, drift in dated]


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
    header = ("shape", "core", "seen", "versions", "bytes", "promote")
    return [header] + [
        (
            drift.shape,
            drift.core,
            str(drift.seen),
            drift.span,
            str(drift.size),
            str(drift.candidate.path),
        )
        for drift in drifts
    ]


def render(rows: list[tuple[str, ...]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "".join(
        "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() + "\n"
        for row in rows
    )


def main() -> None:
    argv = sys.argv[1:]
    drift_only = "--drift" in argv
    filters = [arg for arg in argv if arg != "--drift"]
    raws = sorted(CAPTURES_DIR.glob("*.raw.md"))
    assert raws, CAPTURES_DIR
    captures = [
        parse_name(path)
        for path in raws
        if not filters or any(f in path.name for f in filters)
    ]
    kb_texts = {
        p.stem: p.read_text()
        for p in sorted(KB_DIR.iterdir())
        if p.suffix == ".md" and p.name != "CLAUDE.md"
    }

    blocks = rule_templates.load_templates(prompt_patches.BLOCKS_DIR)
    rows = survey(captures, kb_texts, blocks)

    if drift_only:
        drifts = drifted(rows, promoted_cores(kb_texts, blocks))
        if not drifts:
            print(f"no uncovered prompt copies in {len(rows)} captures")
            return
        sys.stdout.write(render(drift_table(drifts)))
        print(
            f"\n{len(drifts)} uncovered copies."
            " Each shape's newest is the promotion due; weigh it against `seen`,"
            " since a one-off can be newer than the copy that keeps recurring."
        )
    else:
        sys.stdout.write(render(inventory_table(rows)))


if __name__ == "__main__":
    main()
