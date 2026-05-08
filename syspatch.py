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
    match: str
    replace: str
    conditional: bool

    @staticmethod
    def load(directory: Path) -> Patch:
        name = directory.name
        match_file = directory / "match.md"
        replace_file = directory / "replace.md"
        conditional_file = directory / "conditional.bool"

        assert match_file.exists(), (name, match_file)
        assert replace_file.exists(), (name, replace_file)

        match = match_file.read_text()
        replace = replace_file.read_text()
        conditional = _read_bool(conditional_file)

        return Patch(
            name=name,
            match=match,
            replace=replace,
            conditional=conditional,
        )


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


def _apply_template_patch(text: str, patch: Patch) -> str | None:
    """Apply a template patch. Returns new text or None if no match."""
    pattern = _template_to_regex(patch.match)
    m = pattern.search(text)
    if m is None:
        return None
    return text[: m.start()] + patch.replace + text[m.end() :]


def load_patches(patches_dir: Path) -> tuple[Patch, ...]:
    if not patches_dir.is_dir():
        return ()
    patches = []
    for child in sorted(patches_dir.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "match.md").exists():
            continue
        patches.append(Patch.load(child))
    return tuple(patches)


def apply_patches(text: str, patches: tuple[Patch, ...]) -> str:
    for patch in patches:
        result = _apply_template_patch(text, patch)
        if result is None:
            if not patch.conditional:
                print(
                    f"WARNING: patch {patch.name!r} failed to match",
                    file=sys.stderr,
                )
            continue
        text = result
        print(f"applied patch: {patch.name}", file=sys.stderr)
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
        label = "conditional" if patch.conditional else "required"
        print(f"  {patch.name} ({label})", file=sys.stderr)


def request(flow):
    from mitmproxy import http

    assert isinstance(flow, http.HTTPFlow)

    content_bytes = flow.request.get_content()
    if not content_bytes:
        return

    try:
        body = json.loads(content_bytes)
    except json.JSONDecodeError:
        return

    system = body.get("system")
    if system is None:
        return

    if isinstance(system, str):
        body["system"] = apply_patches(system, PATCHES)
    elif isinstance(system, list):
        for item in system:
            if isinstance(item, dict) and item.get("type") == "text":
                item["text"] = apply_patches(item["text"], PATCHES)
    else:
        raise AssertionError(("unexpected system type", type(system)))

    flow.request.set_content(json.dumps(body).encode())
