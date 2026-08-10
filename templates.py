"""Compile declarative templates -- literal prose with `$PLACEHOLDER` holes --
into regexes, and apply directories of them to a body.

Two consumers with opposite loudness disciplines share this: `syspatch.py`
rewrites prompts and is loud when a rule half-applies, while `incidents.py`
masks session-volatile text out of the capture digest and is never loud.
Applying a rule set therefore *returns* what failed to apply instead of
reporting it -- keeping this module ignorant of `incidents.py` is what lets
`incidents.py` import it without a cycle.

Format spec: `~/.claude/system-prompt-patches.d/README.md` for the patch
dialect, `masks.d/README.md` for the mask dialect (a bare template, rewriting
every occurrence to itself).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

# Matches $ALLCAPS placeholders in templates (trailing digits allowed:
# $LINES1/$LINES2 are distinct placeholders of the LINES type)
PLACEHOLDER_RE = re.compile(r"\$([A-Z]+[0-9]*)")

# Pattern for $LINES: one or more non-empty lines (no trailing newline)
LINES_PATTERN = r"[^\n]+(?:\n[^\n]+)*"

# Pattern for $...BLOCK: the rest of a top-level section -- any text, blank
# lines included, stopping before the next "# " heading (or end of body).
BLOCK_PATTERN = r"(?:(?!\n# ).)*"

# Pattern for other placeholders: rest of line (possibly empty)
DEFAULT_PATTERN = r"[^\n]*"


class Miss(NamedTuple):
    """A rule that didn't apply, and how. Deliberately not `incidents.Incident`
    -- identical shape, but this module must not depend on the reporting side;
    callers that care convert."""

    rule: str
    kind: str


class Template(NamedTuple):
    """A named template with no replacement text, because what a whole
    directory of them does is fixed by the directory: `masks.d/` rewrites each
    hit to the template itself, `blocks.d/` deletes it. See their READMEs."""

    name: str
    template: str


class Rule(NamedTuple):
    name: str
    # match.md/match.d: is this rule applicable here at all?
    matches: tuple[str, ...]
    # search.md/search.d: exact text to replace; () means "whichever match hit"
    search: tuple[str, ...]
    replace: str | None  # None when upstream_removed
    upstream_removed: bool

    @staticmethod
    def load(directory: Path) -> Rule:
        name = directory.name
        replace_file = directory / "replace.md"

        matches = _load_alternatives(directory, "match")
        assert matches, (directory, "missing match.md or match.d/")
        search = _load_alternatives(directory, "search")
        upstream_removed = _read_bool(directory / "upstream-removed.bool")

        if upstream_removed:
            assert not replace_file.exists(), (
                name,
                "replace.md must be absent when upstream-removed",
            )
            assert not search, (
                name,
                "search.md/search.d is meaningless when upstream-removed (no replace happens)",
            )
            replace = None
        else:
            assert replace_file.exists(), (name, replace_file)
            replace = replace_file.read_text()

        return Rule(
            name=name,
            matches=matches,
            search=search,
            replace=replace,
            upstream_removed=upstream_removed,
        )


def _load_alternatives(directory: Path, base_name: str) -> tuple[str, ...]:
    """Load templates from `{base_name}.md` (single) or `{base_name}.d/*.md`
    (alternatives, tried in sorted-filename order, first hit wins). Returns
    () if neither is present -- callers decide whether that's required
    (match) or an optional default (search)."""
    single_file = directory / f"{base_name}.md"
    multi_dir = directory / f"{base_name}.d"
    has_file = single_file.is_file()
    has_dir = multi_dir.is_dir()

    assert not (has_file and has_dir), (
        directory,
        f"both {base_name}.md and {base_name}.d/ present",
    )

    if has_file:
        return (single_file.read_text(),)
    if not has_dir:
        return ()

    files = sorted(p for p in multi_dir.iterdir() if p.is_file() and p.suffix == ".md")
    assert files, (multi_dir, f"no *.md files in {base_name}.d/")
    return tuple(p.read_text() for p in files)


def _read_bool(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text().strip().lower()
    match text:
        case "true" | "1" | "yes":
            return True
        case "false" | "0" | "no" | "":
            return False
        case _:
            raise AssertionError(("unexpected bool value", path, text))


def placeholder_pattern(name: str) -> str:
    base = name.rstrip("0123456789")
    if base.endswith("BLOCK"):
        return BLOCK_PATTERN
    elif base.endswith("LINES"):
        return LINES_PATTERN
    else:
        return DEFAULT_PATTERN


def template_to_regex(template: str) -> re.Pattern[str]:
    """Convert a template with $PLACEHOLDER tokens to a compiled regex.

    Same-named placeholders must match the same text (backreference); use
    distinct names for independent matches. The name's suffix (ignoring
    trailing digits) picks what it matches: LINES is one or more non-empty
    lines, BLOCK is the rest of a top-level section, anything else is the
    rest of the line. The type is a suffix rather than the whole name because
    a mask's placeholder name is what a reader sees in the masked text, so it
    has to be able to say what was masked.
    """
    parts = PLACEHOLDER_RE.split(template)
    # parts alternates: [literal, name, literal, name, ..., literal]
    regex_parts: list[str] = []
    seen: set[str] = set()

    for i, part in enumerate(parts):
        if i % 2 == 0:
            regex_parts.append(re.escape(part))
        elif part in seen:
            regex_parts.append(f"(?P={part})")
        else:
            seen.add(part)
            regex_parts.append(f"(?P<{part}>{placeholder_pattern(part)})")

    return re.compile("".join(regex_parts), re.DOTALL)


def expand_replace(template: str, target: re.Match[str]) -> str:
    """$NAME tokens in replace text re-emit what the search's same-named
    placeholder captured -- the only way a rewrite can keep dynamic content
    (session paths, branch names) it cannot know ahead of time. A name the
    search didn't capture is a rule-config error, not drift: fail hard."""
    parts = PLACEHOLDER_RE.split(template)
    # parts alternates: [literal, name, literal, name, ..., literal]
    return "".join(
        part if i % 2 == 0 else target.group(part) for i, part in enumerate(parts)
    )


def first_hit(text: str, templates: tuple[str, ...]) -> re.Match[str] | None:
    """Try each template against text in order, return the first `re.Match`,
    or None if none hit. Shared by match (applicability) and search (replace
    target) -- both are "try these alternatives, first one wins"."""
    for template in templates:
        pattern = template_to_regex(template)
        m = pattern.search(text)
        if m is not None:
            return m
    return None


def load_rules(rules_dir: Path) -> tuple[Rule, ...]:
    """Every subdirectory of rules_dir is a rule: Rule.load asserts on a
    malformed one (missing match.md/match.d/) rather than this function
    silently dropping it -- a config error, not out-of-scope.

    An absent directory or an empty result is likewise a config error, not
    "nothing to do". The patches dir is `~`-relative, so a wrong $HOME
    resolves it somewhere that doesn't exist; returning () there would make
    a broken environment measure as a clean zero-strip run.
    """
    assert rules_dir.is_dir(), (rules_dir, "rules dir missing (wrong $HOME?)")
    rules = tuple(
        Rule.load(child) for child in sorted(rules_dir.iterdir()) if child.is_dir()
    )
    assert rules, (rules_dir, "no rules found")
    return rules


def load_templates(directory: Path) -> tuple[Template, ...]:
    """One template per `*.md` file, named by its stem: the whole file is the
    template, and there is nowhere to put a replacement, a search, or an
    upstream-removed flag. See `masks.d/README.md` for why each of those is
    withheld rather than ignored."""
    files = sorted(
        p for p in directory.glob("*.md") if p.is_file() and p.name != "README.md"
    )
    assert files, (directory, "no templates found")
    templates = tuple(Template(p.stem, p.read_text()) for p in files)
    for template in templates:
        # A template of nothing but placeholders matches the empty string
        # everywhere, and every occurrence of that is every position in the
        # body. Requiring an anchor is what makes "rewrite every hit" safe.
        literals = "".join(PLACEHOLDER_RE.split(template.template)[::2])
        assert literals.strip(), (template.name, "all placeholder: no anchor text")
    return templates


def load_masks(masks_dir: Path) -> tuple[Template, ...]:
    """Templates from masks_dir, rejecting the one placeholder type a mask
    must not have: $...BLOCK spans a whole section, so a mask carrying one
    would swap real prose for a token instead of neutralizing a value, and
    the digest would stop noticing copy it is supposed to notice."""
    masks = load_templates(masks_dir)
    for mask in masks:
        wide = [
            name
            for name in PLACEHOLDER_RE.findall(mask.template)
            if placeholder_pattern(name) == BLOCK_PATTERN
        ]
        assert not wide, (mask.name, wide, "a mask may not span a whole block")
    return masks


def borrow_newline(text: str) -> tuple[str, bool]:
    """Templates ending in `\\n` must be able to match a block that sits at
    end-of-body; without a trailing newline `$LINES\\n` backtracks one line
    short. Callers undo this before returning -- leaving it makes an all-miss
    run differ from its input by a byte, which reads as a rule firing.

    Public because measuring where a rule *would* match has to be done against
    the same text the appliers below see, off-by-one newline included."""
    if text.endswith("\n"):
        return text, False
    return text + "\n", True


def apply_rules(text: str, rules: tuple[Rule, ...]) -> tuple[str, list[Miss]]:
    """Apply each rule at most once, in order, returning the rewritten text
    and the rules that didn't apply cleanly. A `match` miss is not a Miss:
    that's the mechanism by which a rule detects its own irrelevance."""
    text, borrowed = borrow_newline(text)
    misses: list[Miss] = []
    for rule in rules:
        m = first_hit(text, rule.matches)
        if m is None:
            # match didn't find its target: this rule isn't applicable here
            # (wrong prompt variant, session-optional content absent,
            # whatever). Always silent -- a non-match is not a failure, it's
            # the mechanism by which a rule detects its own relevance.
            continue
        if rule.upstream_removed:
            misses.append(Miss(rule.name, "matched-despite-upstream-removed"))
            continue
        if not rule.search:
            target = m
        else:
            target = first_hit(text, rule.search)
            if target is None:
                # match succeeded (we're in scope) but none of search's
                # alternatives found their precise target -- the caller's cue
                # to be loud. Unlike a match miss, this means the rule's own
                # precondition holds yet its target vanished: real drift.
                misses.append(Miss(rule.name, "failed-to-match"))
                continue
        assert rule.replace is not None  # invariant: only None when upstream_removed
        replacement = expand_replace(rule.replace, target)
        text = text[: target.start()] + replacement + text[target.end() :]
    if borrowed and text.endswith("\n"):
        text = text[:-1]
    return text, misses


def strip_blocks(text: str, blocks: tuple[Template, ...]) -> tuple[str, list[str]]:
    """Text with every session-optional block deleted, and the names of the
    blocks that were there. Deleting is the whole point -- unlike a mask, a
    block rule answers "would this body be the same if the session hadn't
    switched this on?", so the result must be byte-identical to a body that
    never carried the block."""
    text, borrowed = borrow_newline(text)
    present = []
    for block in blocks:
        stripped = template_to_regex(block.template).sub("", text)
        if stripped != text:
            present.append(block.name)
        text = stripped
    if borrowed and text.endswith("\n"):
        text = text[:-1]
    return text, present


def apply_masks(text: str, masks: tuple[Template, ...]) -> str:
    """Rewrite every occurrence of every mask to the mask's own template, so
    each placeholder's captured text is replaced by the placeholder's name.

    Two differences from `apply_rules` earn their own function. Every
    occurrence, not the first: a rendered multi-block capture repeats the
    same session paths per block, and one surviving copy is enough to fork
    the digest. And the template is emitted verbatim, never expanded, which
    is what makes a mask unable to delete text it didn't capture."""
    text, borrowed = borrow_newline(text)
    for mask in masks:
        text = template_to_regex(mask.template).sub(
            lambda _hit, template=mask.template: template, text
        )
    if borrowed and text.endswith("\n"):
        text = text[:-1]
    return text
