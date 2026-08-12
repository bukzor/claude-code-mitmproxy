#!/usr/bin/env python3
"""Whether the system-prompt patch set still lands on the current prompt.

A `failed-to-match` miss is the loud path's own definition of drift: the rule's
`match` proved it is in scope and then its `search` target had vanished. The
live proxy files an incident for exactly this, once, on the machine that pays
for it. Checking here catches it on the machine that promoted the fixture
instead -- run it after promoting one, or after editing a patch.

The newest full fixture only, deliberately: an older one predates every
upstream removal, so sunset rules still match it and report a miss that means
nothing (see `corpus.latest_fixture`).

To read the patched prompt itself rather than its measurements, that is
`render_patched.py`.

Usage: check_patches.py [--data-only]

Structure is `verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from claude_mitmproxy import corpus
from claude_mitmproxy import syspatch
from claude_mitmproxy import templates
from claude_mitmproxy import verdict


class Patched(NamedTuple):
    source: Path
    original: int  # chars upstream sends
    patched: int  # chars the session receives
    misses: tuple[templates.Miss, ...]


def collect() -> Patched:
    source = corpus.latest_fixture()
    text = source.read_text()
    patches = templates.load_rules(syspatch.PATCHES_DIR)
    # `apply_rules`, not `syspatch.apply_patches`: measuring is not triaging,
    # and a miss provoked here must not file an incident for someone to
    # discover as if a session had hit it.
    patched, misses = templates.apply_rules(text, patches)
    return Patched(source, len(text), len(patched), tuple(misses))


def render(patched: Patched) -> str:
    return (
        f"{patched.source.stem}: {patched.original} -> {patched.patched} chars"
        f" ({patched.patched - patched.original:+d})\n"
    )


def patches_that_miss(patched: Patched) -> list[str]:
    """patch rules that proved themselves in scope and then found nothing to
    replace. This is drift: the rule still recognizes the prompt, so it is
    aimed at the right session, but the text it was written against is gone.
    Every session gets the unpatched prompt until someone rewrites the rule."""
    return [f"{miss.rule}: {miss.kind}" for miss in patched.misses]


def net_growth(patched: Patched) -> list[str]:
    """the net size change, when the patch set fails to shorten the prompt.
    Subtraction is the whole point of the patch set, so a run that nets out
    longer means a replacement grew past what it replaced -- worth a look even
    when every rule still matches, since nothing else measures it."""
    if patched.patched < patched.original:
        return []
    return [f"{patched.original} -> {patched.patched} chars"]


PREDICATES = (patches_that_miss, net_growth)


def main(argv: list[str] | None = None) -> int:
    return verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
