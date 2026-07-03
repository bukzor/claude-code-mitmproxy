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
    matches: tuple[str, ...]  # match.md/match.d: is this patch applicable here at all?
    search: tuple[str, ...]  # search.md/search.d: exact text to replace; () means "whichever match template hit"
    replace: str | None  # None when upstream_removed
    upstream_removed: bool

    @staticmethod
    def load(directory: Path) -> Patch:
        name = directory.name
        replace_file = directory / "replace.md"

        matches = _load_templates(directory, "match")
        assert matches, (directory, "missing match.md or match.d/")
        search = _load_templates(directory, "search")
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

        return Patch(
            name=name,
            matches=matches,
            search=search,
            replace=replace,
            upstream_removed=upstream_removed,
        )


def _load_templates(directory: Path, base_name: str) -> tuple[str, ...]:
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


def _first_hit(text: str, templates: tuple[str, ...]) -> re.Match[str] | None:
    """Try each template against text in order, return the first `re.Match`,
    or None if none hit. Shared by match (applicability) and search (replace
    target) -- both are "try these alternatives, first one wins"."""
    for template in templates:
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
BODIES_DIRNAME = "_bodies"

# Per-session-volatile regions that differ between otherwise-identical bodies
# (cwd, scratchpad path, git status + recent commits). Neutralized only for the
# dedup hash; the stored body keeps them verbatim for diagnosis.
_VOLATILE_SUBS = (
    (re.compile(r"\ngitStatus:.*", re.DOTALL), "\n"),
    (re.compile(r"(?m)^( - Primary working directory:).*"), r"\1"),
    (re.compile(r"(?m)^`/tmp/.*scratchpad`$"), "`scratchpad`"),
)


def content_hash(body: str) -> str:
    """Hash identifying the prompt *content*, stable across sessions: the
    per-session environment tail (cwd, scratchpad path, git status) is
    neutralized first, so the same prompt dedups to a single incident instead
    of one per session that happened to run it from a different directory."""
    normalized = body
    for pattern, repl in _VOLATILE_SUBS:
        normalized = pattern.sub(repl, normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


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
        m = _first_hit(text, patch.matches)
        if m is None:
            # match didn't find its target: this patch isn't applicable here
            # (wrong prompt variant, session-optional content absent,
            # whatever). Always silent -- a non-match is not a failure, it's
            # the mechanism by which a patch detects its own relevance.
            continue
        if patch.upstream_removed:
            issues.append(PatchIssue(patch.name, "matched-despite-upstream-removed"))
            continue
        if not patch.search:
            target = m
        else:
            target = _first_hit(text, patch.search)
            if target is None:
                # match succeeded (we're in scope) but none of search's
                # alternatives found their precise target -- always loud, no
                # override. Unlike a match miss, this means the patch's own
                # precondition holds yet its target vanished: a real
                # drift/regression to triage.
                issues.append(PatchIssue(patch.name, "failed-to-match"))
                continue
        assert patch.replace is not None  # invariant: only None when upstream_removed
        text = text[: target.start()] + patch.replace + text[target.end() :]
    if issues:
        report_issues(original, issues, capture_dir)
    return text


def report_issues(body: str, issues: list[PatchIssue], capture_dir: Path | None) -> None:
    """Warn about patches that didn't apply cleanly; when capture_dir is given,
    save the body once (content-addressed) plus one incident record per
    (patch, content) so it can be diagnosed later.

    Capture is idempotent on disk: a body whose content was already recorded
    re-saves nothing and re-warns nothing. The live proxy patches every request,
    so this is what keeps a persistent mismatch from logging endlessly — the
    first request captures and warns, the rest find the record present.
    """
    if capture_dir is None:
        for issue in issues:
            logging.warning("patch %r %s", issue.patch, issue.kind)
        return

    digest = content_hash(body)
    save_body(body, digest, capture_dir)
    for issue in issues:
        saved = save_incident(issue, digest, capture_dir)
        # logging (not stderr): the console TUI routes records to its event log /
        # status bar; raw stderr corrupts curses. Warn only on a fresh capture.
        if saved is not None:
            logging.warning("patch %r %s -> %s", issue.patch, issue.kind, saved)


def save_body(body: str, digest: str, capture_dir: Path) -> Path:
    """Store the offending body once at capture_dir/_bodies/{digest}.md, where
    digest is its content_hash. No-op if already present. The file holds the
    verbatim body (one representative session's environment); the digest keys
    its content, so it is not a checksum of the bytes on disk."""
    bodies_dir = capture_dir / BODIES_DIRNAME
    bodies_dir.mkdir(parents=True, exist_ok=True)
    body_path = bodies_dir / f"{digest}.md"
    if not body_path.exists():
        body_path.write_text(body)
    return body_path


def save_incident(issue: PatchIssue, digest: str, capture_dir: Path) -> Path | None:
    """Write one incident at capture_dir/{rule}/{digest}.json, referencing the
    shared body. Returns the path when freshly written, None when this
    (patch, content) was already recorded — so the caller warns exactly once
    per distinct failure, across restarts."""
    rule_dir = capture_dir / issue.patch
    rule_dir.mkdir(parents=True, exist_ok=True)
    meta_path = rule_dir / f"{digest}.json"
    if meta_path.exists():
        return None
    meta = {
        "at": datetime.now(timezone.utc).isoformat(),
        "rule": issue.patch,
        "kind": issue.kind,
        "body": digest,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return meta_path


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
        elif patch.search:
            label = "match+search"
        else:
            label = "match-only"
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
