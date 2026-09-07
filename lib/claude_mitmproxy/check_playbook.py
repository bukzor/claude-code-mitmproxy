"""Does `playbook.kb/` say what every watch line means?

Every line the watch prints that asks something of a reader starts with its
event type, and that type is the name of the entry saying what addressing it
means (`design/040-design.kb/events-are-separate-from-logs.md`). The
correspondence is between the taxonomy in `logging_handlers.events` and a
directory of files, and nothing but a check holds it: a type added without
an entry sends a reader to a file that is not there, and an entry a rename
left behind is a procedure nobody will find again. Fired by the commit that
touches either side (`.pre-commit-config.yaml`).
"""

from __future__ import annotations

from typing import NamedTuple

from claude_mitmproxy import check_verdict
from claude_mitmproxy import logging_handlers
from claude_mitmproxy import repo_paths

PLAYBOOK_DIR = repo_paths.ROOT / "playbook.kb"
# The collection's maintenance guide (Skill(llm-kb)): the one file there that
# is not an entry.
GUIDE = "CLAUDE.md"


class Correspondence(NamedTuple):
    types: frozenset[str]  # what the taxonomy publishes, as `event_key` spells it
    entries: frozenset[str]  # what `playbook.kb/` has an entry for, by stem


def collect() -> Correspondence:
    entries = {path.stem for path in PLAYBOOK_DIR.glob("*.md") if path.name != GUIDE}
    return Correspondence(frozenset(logging_handlers.event_keys()), frozenset(entries))


def render(found: Correspondence) -> str:
    """Both sides, since a green run is silent about how many keys it held together."""
    return f"{len(found.types)} event types, {len(found.entries)} entries in {PLAYBOOK_DIR.name}/\n"


def types_without_an_entry(found: Correspondence) -> list[str]:
    """Event types with no `playbook.kb/<type>.md`. A line keyed by one of
    these sends its reader to a file that does not exist -- a published name
    that leads nowhere, one rung out from a taxonomy name with no emitter."""
    return sorted(found.types - found.entries)


def entries_without_a_type(found: Correspondence) -> list[str]:
    """Playbook entries naming no event type. Nothing will ever print the key,
    so nothing will ever lead a reader here: a rename that left its procedure
    behind, or an entry written for a type that was never added."""
    return sorted(found.entries - found.types)


PREDICATES = (types_without_an_entry, entries_without_a_type)


def main(argv: list[str] | None = None) -> int:
    return check_verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
