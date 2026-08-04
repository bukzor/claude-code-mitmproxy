#!/usr/bin/env python3
"""Inventory of captured system-prompt bodies: one row per raw capture in
log/prompt-captures/, classified by prompt shape, with the session-optional
blocks it carries and whether its exact body is already promoted into
system-prompts.kb/. This serves the standing promotion duty ("check for
cc_versions newer than the newest full-body capture") -- promotion has no
automatic trigger, so this table is the "someone looks" step.

Usage: survey_captures.py [SUBSTRING ...]
Rows are filtered to filenames containing any SUBSTRING (e.g. "2.1.221").
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

CAPTURES_DIR = Path("log/prompt-captures")
KB_DIR = Path("system-prompts.kb")

# First matching heading wins; distinguishing headings per known shape.
SHAPE_MARKERS = (
    ("# Communicating with the user", "harness-fable"),
    ("# Delivering work", "harness-opus"),
    ("# Harness", "harness"),  # pre-split (< v2.1.221) Fable-class shape
    ("# Doing tasks", "long-form"),
)

# Session-optional blocks worth surfacing when choosing which capture to
# promote: fuller captures (more blocks) make better fixtures.
BLOCK_MARKERS = (
    ("gitStatus:", "git"),
    ("Git user:", "gituser"),
    ("Additional working directories", "adddirs"),
    ("# Memory", "mem"),
    ("# auto memory", "automem"),
    ("# Scratchpad Directory", "scratch"),
)


class Capture(NamedTuple):
    version: str  # cc_version incl. build tag, e.g. "2.1.221.b87"
    model: str
    digest: str
    path: Path

    @property
    def sort_key(self) -> tuple:
        release, _, build = self.version.rpartition(".")
        return tuple(int(part) for part in release.split(".")) + (build, self.model)


def parse_name(path: Path) -> Capture:
    stem = path.name.removesuffix(".raw.md")
    version, model, digest = stem.rsplit("_", 2)
    assert version.startswith("v"), path
    return Capture(version.removeprefix("v"), model, digest, path)


def shape_of(text: str) -> str:
    for marker, shape in SHAPE_MARKERS:
        if f"\n{marker}\n" in text or text.startswith(f"{marker}\n"):
            return shape
    first_heading = next(
        (line for line in text.splitlines() if line.startswith("#")), "(none)"
    )
    return f"?{first_heading!r}"


def blocks_of(text: str) -> str:
    # "#"-markers are headings and must match a whole line -- substring
    # matching would false-positive on subheadings like "## Memory and
    # other forms of persistence".
    lines = set(text.splitlines())
    return ",".join(
        flag
        for marker, flag in BLOCK_MARKERS
        if (marker in lines if marker.startswith("#") else marker in text)
    )


def promoted_as(text: str, kb_texts: dict[str, str]) -> str:
    return next((name for name, kb in kb_texts.items() if kb == text), "")


def main() -> None:
    filters = sys.argv[1:]
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

    header = ("version", "model", "digest", "bytes", "shape", "promoted", "blocks")
    rows = [header]
    for capture in sorted(captures, key=lambda c: c.sort_key):
        text = capture.path.read_text()
        rows.append((
            capture.version,
            capture.model.removeprefix("claude-"),
            capture.digest,
            str(len(text)),
            shape_of(text),
            promoted_as(text, kb_texts),
            blocks_of(text),
        ))

    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())


if __name__ == "__main__":
    main()
