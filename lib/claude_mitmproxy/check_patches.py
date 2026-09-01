#!/usr/bin/env python3
"""Whether the system-prompt patch set still lands on the current prompt.

A `failed-to-match` miss is the loud path's own definition of drift: the rule's
`match` proved it is in scope and then its `search` target had vanished. The
live proxy files an incident for exactly this, once, on the machine that pays
for it. Checking here catches it on the machine that promoted the fixture
instead -- run it after promoting one, or after editing a patch.

Every full fixture at the newest release, and only those: an older one
predates every upstream removal, so sunset rules still match it and report a
miss that means nothing, while one body at the current release is not the
current prompt -- upstream serves several at once, and a patch that misses on
any of them misses in production (see `prompt_corpus.current_fixtures`).

To read the patched prompt itself rather than its measurements, that is
`render_patched.py`.

Usage: check_patches.py [--data-only]

Structure is `check_verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from claude_mitmproxy import prompt_corpus
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates
from claude_mitmproxy import check_verdict


class Patched(NamedTuple):
    source: Path
    original: int  # chars upstream sends
    patched: int  # chars the session receives
    misses: tuple[rule_templates.Miss, ...]


def collect() -> tuple[Patched, ...]:
    patches = rule_templates.load_rules(prompt_patches.PATCHES_DIR)
    rows = []
    for source in prompt_corpus.current_fixtures():
        text = source.read_text()
        # `apply_rules`, not `prompt_patches.apply_patches`: measuring is not
        # triaging, and a miss provoked here must not file an incident for
        # someone to discover as if a session had hit it.
        patched, misses = rule_templates.apply_rules(text, patches)
        rows.append(Patched(source, len(text), len(patched), tuple(misses)))
    return tuple(rows)


def render(rows: tuple[Patched, ...]) -> str:
    """One line per body upstream is serving at this release, so a run says how
    many were checked rather than leaving that to the reader's assumption."""
    return "".join(
        f"{row.source.stem}: {row.original} -> {row.patched} chars"
        f" ({row.patched - row.original:+d})\n"
        for row in rows
    )


def patches_that_miss(rows: tuple[Patched, ...]) -> list[str]:
    """patch rules that proved themselves in scope and then found nothing to
    replace. This is drift: the rule still recognizes the prompt, so it is
    aimed at the right session, but the text it was written against is gone.
    Every session gets the unpatched prompt until someone rewrites the rule.

    Named by fixture: at one release the same rule can land on one copy and
    miss another, and which body it missed is where triage starts."""
    return [
        f"{row.source.stem}: {miss.rule}: {miss.kind}"
        for row in rows
        for miss in row.misses
    ]


def net_growth(rows: tuple[Patched, ...]) -> list[str]:
    """the net size change, when the patch set fails to shorten the prompt.
    Subtraction is the whole point of the patch set, so a run that nets out
    longer means a replacement grew past what it replaced -- worth a look even
    when every rule still matches, since nothing else measures it."""
    return [
        f"{row.source.stem}: {row.original} -> {row.patched} chars"
        for row in rows
        if row.patched >= row.original
    ]


PREDICATES = (patches_that_miss, net_growth)


def main(argv: list[str] | None = None) -> int:
    return check_verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
