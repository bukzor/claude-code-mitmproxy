"""Apply modular patches to the Claude Code system prompt via mitmproxy."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Matches $ALLCAPS placeholders in templates
PLACEHOLDER_RE = re.compile(r"\$([A-Z]+)")

# Pattern for $LINES: one or more non-empty lines (no trailing newline)
LINES_PATTERN = r"[^\n]+(?:\n[^\n]+)*"

# Pattern for other placeholders: rest of line (possibly empty)
DEFAULT_PATTERN = r"[^\n]*"


class Patch(NamedTuple):
    name: str
    matches: tuple[str, ...]
    replace: str | None  # None when upstream_removed
    conditional: bool
    upstream_removed: bool

    @staticmethod
    def load(directory: Path) -> Patch:
        name = directory.name
        replace_file = directory / "replace.md"

        matches = _load_matches(directory)
        upstream_removed = _read_bool(directory / "upstream-removed.bool")
        conditional = _read_bool(directory / "conditional.bool")

        assert not (upstream_removed and conditional), (
            name,
            "upstream-removed and conditional are mutually exclusive",
        )
        if upstream_removed:
            assert not replace_file.exists(), (
                name,
                "replace.md must be absent when upstream-removed",
            )
            replace = None
        else:
            assert replace_file.exists(), (name, replace_file)
            replace = replace_file.read_text()

        return Patch(
            name=name,
            matches=matches,
            replace=replace,
            conditional=conditional,
            upstream_removed=upstream_removed,
        )


def _load_matches(directory: Path) -> tuple[str, ...]:
    """Load match templates from `match.md` (single) or `match.d/*.md` (alternatives).

    Exactly one form must be present. Inside `match.d/`, only `*.md` files are read,
    in sorted-filename order. Alternatives are tried in order at apply time.
    """
    match_file = directory / "match.md"
    match_dir = directory / "match.d"
    has_file = match_file.is_file()
    has_dir = match_dir.is_dir()

    assert has_file or has_dir, (directory, "missing match.md or match.d/")
    assert not (has_file and has_dir), (
        directory,
        "both match.md and match.d/ present",
    )

    if has_file:
        return (match_file.read_text(),)

    files = sorted(p for p in match_dir.iterdir() if p.is_file() and p.suffix == ".md")
    assert files, (match_dir, "no *.md files in match.d/")
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


def _template_to_regex(template: str) -> re.Pattern[str]:
    """Convert a template with $PLACEHOLDER tokens to a compiled regex.

    Same-named placeholders must capture the same text (via backreference).
    $LINES matches one or more non-empty lines.
    Other $NAMES match any non-empty text (non-greedy).
    """
    parts = PLACEHOLDER_RE.split(template)
    # parts alternates: [literal, name, literal, name, ..., literal]
    regex_parts: list[str] = []

    for i, part in enumerate(parts):
        if i % 2 == 0:
            regex_parts.append(re.escape(part))
        else:
            pattern = LINES_PATTERN if part == "LINES" else DEFAULT_PATTERN
            regex_parts.append(f"(?:{pattern})")

    return re.compile("".join(regex_parts), re.DOTALL)


def _find_first_match(text: str, patch: Patch) -> re.Match[str] | None:
    """Return the first matching template's `re.Match`, or None if none match."""
    for template in patch.matches:
        pattern = _template_to_regex(template)
        m = pattern.search(text)
        if m is not None:
            return m
    return None


def load_patches(patches_dir: Path) -> tuple[Patch, ...]:
    if not patches_dir.is_dir():
        return ()
    patches = []
    for child in sorted(patches_dir.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "match.md").exists() and not (child / "match.d").is_dir():
            continue
        patches.append(Patch.load(child))
    return tuple(patches)


def apply_patches(text: str, patches: tuple[Patch, ...]) -> str:
    for patch in patches:
        m = _find_first_match(text, patch)
        if patch.upstream_removed:
            if m is not None:
                print(
                    f"WARNING: patch {patch.name!r} marked upstream-removed but matched body",
                    file=sys.stderr,
                )
            continue
        if m is None:
            if not patch.conditional:
                print(
                    f"WARNING: patch {patch.name!r} failed to match",
                    file=sys.stderr,
                )
            continue
        assert patch.replace is not None  # invariant: only None when upstream_removed
        text = text[: m.start()] + patch.replace + text[m.end() :]
    return text


# --- mitmproxy addon ---

PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()
PATCHES: tuple[Patch, ...] = ()


def load(loader):
    """Called once at mitmproxy startup."""
    global PATCHES
    PATCHES = load_patches(PATCHES_DIR)
    print(f"loaded {len(PATCHES)} system prompt patches", file=sys.stderr)
    for patch in PATCHES:
        if patch.upstream_removed:
            label = "upstream-removed"
        elif patch.conditional:
            label = "conditional"
        else:
            label = "required"
        print(f"  {patch.name} ({label})", file=sys.stderr)


def request(flow):
    from mitmproxy import http

    assert isinstance(flow, http.HTTPFlow)

    content_bytes = flow.request.get_content()
    if not content_bytes:
        return

    try:
        request = json.loads(content_bytes)
    except json.JSONDecodeError:
        return

    system = request.get("system")
    if system is None:
        return

    if isinstance(system, str):
        request["system"] = apply_patches(system, PATCHES)
    elif isinstance(system, list):
        system = [
            item
            for item in system
            if isinstance(item, dict)
            and item.get("type") == "text"
            and item.get("text", "").startswith("\nYou are an interactive agent")
        ]
        assert len(system) == 1, (
            "expected 1 system-prompt body, found",
            len(system),
            system,
        )
        system = system[0]
        system["text"] = apply_patches(system["text"], PATCHES)
    else:
        raise AssertionError(("unexpected system type", type(system)))

    flow.request.set_content(json.dumps(request).encode())
