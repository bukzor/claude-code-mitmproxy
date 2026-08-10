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

import incidents
import shapes
import templates

CAPTURES_DIR = Path("log/prompt-captures")
KB_DIR = Path("system-prompts.kb")
BLOCKS_DIR = Path(__file__).parent / "blocks.d"


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


def core_of(text: str, blocks: tuple[templates.Template, ...]) -> tuple[str, str]:
    """The capture's (core digest, session-optional blocks it carries).

    The core digest is what's left once every block this session happened to
    switch on is deleted: two captures share it exactly when they carry the
    same prompt copy, whatever their sessions differed on. Blocks are stripped
    from the masked body, so a block template can be written against the
    tokens masks leave behind instead of the volatile text they replaced."""
    stripped, present = templates.strip_blocks(incidents.normalize_body(text), blocks)
    return incidents.digest_of(stripped), ",".join(present)


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

    blocks = templates.load_templates(BLOCKS_DIR)

    header = (
        "version", "model", "raw", "core", "bytes", "shape", "promoted", "blocks"
    )
    rows: list[tuple[str, ...]] = [header]
    for capture in sorted(captures, key=lambda c: c.sort_key):
        text = capture.path.read_text()
        core, present = core_of(text, blocks)
        rows.append((
            capture.version,
            capture.model.removeprefix("claude-"),
            capture.raw,
            core,
            str(len(text)),
            shapes.shape_of(text),
            promoted_as(text, kb_texts),
            present,
        ))

    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())


if __name__ == "__main__":
    main()
