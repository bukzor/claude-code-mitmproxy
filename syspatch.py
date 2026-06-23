"""Apply modular patches to the Claude Code system prompt via mitmproxy."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
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


class PatchIssue(NamedTuple):
    patch: str
    kind: str  # "failed-to-match" | "matched-despite-upstream-removed"


# Default location for saved offending bodies. Callers pass capture_dir=None to
# disable capture (offline callers like check_patches only want the warning).
CAPTURE_DIR = Path(__file__).parent / "patch-failures"

# (body_hash, issue) already reported this run. The live proxy patches every
# request, so without this each unmatched patch warns and logs endlessly.
_REPORTED: set[tuple[str, PatchIssue]] = set()


def apply_patches(
    text: str, patches: tuple[Patch, ...], capture_dir: Path | None = CAPTURE_DIR
) -> str:
    # Normalize trailing newline so templates ending with `\n` can match a
    # block that sits at end-of-body. Without this, `$LINES\n` backtracks
    # one line short when the body's final line has no trailing newline.
    if not text.endswith("\n"):
        text += "\n"
    original = text
    issues: list[PatchIssue] = []
    for patch in patches:
        m = _find_first_match(text, patch)
        if patch.upstream_removed:
            if m is not None:
                issues.append(PatchIssue(patch.name, "matched-despite-upstream-removed"))
            continue
        if m is None:
            if not patch.conditional:
                issues.append(PatchIssue(patch.name, "failed-to-match"))
            continue
        assert patch.replace is not None  # invariant: only None when upstream_removed
        text = text[: m.start()] + patch.replace + text[m.end() :]
    if issues:
        report_issues(original, issues, capture_dir)
    return text


def report_issues(body: str, issues: list[PatchIssue], capture_dir: Path | None) -> None:
    """Warn about patches that didn't apply cleanly, once per distinct body+issue.

    When capture_dir is given, the offending body is saved there first so the
    mismatch can be diagnosed and the patch updated later; the warning then
    points at the saved file.
    """
    body_hash = hashlib.sha256(body.encode()).hexdigest()[:12]
    for issue in issues:
        key = (body_hash, issue)
        if key in _REPORTED:
            continue
        _REPORTED.add(key)

        saved = save_incident(body, body_hash, issue, capture_dir) if capture_dir else None
        # logging (not stderr): the console TUI routes records to its event log /
        # status bar; raw stderr corrupts curses. warn flashes the status bar,
        # info keeps the saved-path line to the event log only.
        logging.warning("patch %r %s", issue.patch, issue.kind)
        if saved is not None:
            logging.info("saved offending body -> %s", saved)


def save_incident(body: str, body_hash: str, issue: PatchIssue, capture_dir: Path) -> Path:
    """Write the offending body (.md) and its metadata (.json) under
    capture_dir/{rule}/{date}/{timestamp}.*; return the body path.

    Both are whole-file writes — never appended — so concurrent requests can
    never interleave a partial record. Microsecond timestamps key each incident.
    """
    now = datetime.now(timezone.utc)
    day_dir = capture_dir / issue.patch / now.date().isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    stamp = now.isoformat()
    body_path = day_dir / f"{stamp}.md"
    meta_path = day_dir / f"{stamp}.json"
    meta = {"at": stamp, "rule": issue.patch, "kind": issue.kind, "hash": body_hash}

    body_path.write_text(body)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return body_path


# --- mitmproxy addon ---

PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()
PATCHES: tuple[Patch, ...] = ()


def load(loader):
    """Called once at mitmproxy startup."""
    global PATCHES
    PATCHES = load_patches(PATCHES_DIR)
    logging.info("loaded %d system prompt patches", len(PATCHES))
    for patch in PATCHES:
        if patch.upstream_removed:
            label = "upstream-removed"
        elif patch.conditional:
            label = "conditional"
        else:
            label = "required"
        logging.info("  %s (%s)", patch.name, label)


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
