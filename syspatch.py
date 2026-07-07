"""Apply modular patches to the Claude Code system prompt via mitmproxy."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import NamedTuple

from incidents import CAPTURE_DIR, Incident, capture_uncaught, content_hash, save_body, save_incident

# Matches $ALLCAPS placeholders in templates (trailing digits allowed:
# $LINES1/$LINES2 are distinct placeholders of the LINES type)
PLACEHOLDER_RE = re.compile(r"\$([A-Z]+[0-9]*)")

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

    Same-named placeholders must match the same text (backreference);
    use distinct names for independent matches. Trailing digits vary the
    name without changing the type: $LINES, $LINES2, ... each match one
    or more non-empty lines; non-LINES names match the rest of the line
    (possibly empty).
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
            pattern = LINES_PATTERN if part.rstrip("0123456789") == "LINES" else DEFAULT_PATTERN
            regex_parts.append(f"(?P<{part}>{pattern})")

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


def apply_patches(
    text: str, patches: tuple[Patch, ...], capture_dir: Path | None = CAPTURE_DIR
) -> str:
    # Normalize trailing newline so templates ending with `\n` can match a
    # block that sits at end-of-body. Without this, `$LINES\n` backtracks
    # one line short when the body's final line has no trailing newline.
    if not text.endswith("\n"):
        text += "\n"
    original = text
    issues: list[Incident] = []
    for patch in patches:
        m = _first_hit(text, patch.matches)
        if m is None:
            # match didn't find its target: this patch isn't applicable here
            # (wrong prompt variant, session-optional content absent,
            # whatever). Always silent -- a non-match is not a failure, it's
            # the mechanism by which a patch detects its own relevance.
            continue
        if patch.upstream_removed:
            issues.append(Incident(patch.name, "matched-despite-upstream-removed"))
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
                issues.append(Incident(patch.name, "failed-to-match"))
                continue
        assert patch.replace is not None  # invariant: only None when upstream_removed
        text = text[: target.start()] + patch.replace + text[target.end() :]
    if issues:
        report_issues(original, issues, capture_dir)
    return text


def report_issues(body: str, issues: list[Incident], capture_dir: Path | None) -> None:
    """Warn about rules that didn't apply cleanly; when capture_dir is given,
    save the body once (content-addressed) plus one incident record per
    (rule, content) so it can be diagnosed later.

    Capture is idempotent on disk: a body whose content was already recorded
    re-saves nothing and re-warns nothing. The live proxy patches every request,
    so this is what keeps a persistent mismatch from logging endlessly — the
    first request captures and warns, the rest find the record present.
    """
    if capture_dir is None:
        for issue in issues:
            logging.warning("patch %r %s", issue.rule, issue.kind)
        return

    digest = content_hash(body)
    save_body(body, digest, capture_dir)
    for issue in issues:
        saved = save_incident(issue, digest, capture_dir)
        # logging (not stderr): the console TUI routes records to its event log /
        # status bar; raw stderr corrupts curses. Warn only on a fresh capture.
        if saved is not None:
            logging.warning("patch %r %s -> %s", issue.rule, issue.kind, saved)


# --- mitmproxy addon ---

PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()
PATCHES: tuple[Patch, ...] = ()

# Opening text that identifies the main prompt body among `system` blocks.
BODY_MARKER = "\nYou are an interactive agent"
# Incident rule for a `system` list without exactly one such block.
# Underscore-prefixed, like _bodies, so it can't collide with a patch name.
LOCATOR_RULE = "_locate-system-prompt"

# Auxiliary CLI requests (session-title generation, web-search helper, ...)
# legitimately carry no interactive prompt body. Recognized by shape, not by
# full prompt text: every block must be a billing header, the bare CLI
# identity line, or a known task prompt. A drifted interactive prompt still
# captures -- its body block matches none of these.
CLI_IDENTITY = "You are Claude Code, Anthropic's official CLI for Claude."
AUX_TASK_PREFIXES = (
    "Generate a concise, sentence-case title",
    "You are an assistant for performing a web search tool use",
    "You are a security monitor for autonomous AI coding agents",
)

# Subagent requests (Task-tool invocations) carry a per-agent-type prompt
# template that never uses BODY_MARKER either, but unlike the auxiliary CLI
# shapes above, the template body itself varies arbitrarily by agent type
# (claude-code-guide, Explore, general-purpose, ...) -- too open-ended to
# enumerate block-by-block. Recognize the request instead, via the billing
# header's own subagent flag.
SUBAGENT_MARKER = "cc_is_subagent=true"


def is_auxiliary_system(system: list) -> bool:
    """True when every system block belongs to a recognized non-interactive
    request shape, so a missing prompt body is expected, not an incident."""
    return bool(system) and all(_is_auxiliary_block(item) for item in system)


def is_subagent_request(system: list) -> bool:
    """True when the billing-header block marks this a subagent request --
    its prompt body is agent-type-specific and never carries BODY_MARKER."""
    if not system:
        return False
    first = system[0]
    return (
        isinstance(first, dict)
        and isinstance(first.get("text"), str)
        and first["text"].startswith("x-anthropic-billing-header:")
        and SUBAGENT_MARKER in first["text"]
    )


def _is_auxiliary_block(item) -> bool:
    if not (isinstance(item, dict) and isinstance(item.get("text"), str)):
        return False
    else:
        text = item["text"]
        return (
            text.startswith("x-anthropic-billing-header:")
            or text.strip() == CLI_IDENTITY
            or text.startswith(AUX_TASK_PREFIXES)
        )


def render_system_blocks(system: list) -> str:
    """Flatten a content-blocks `system` list into one capture body: text
    blocks verbatim (so content_hash still neutralizes session-volatile
    regions), anything else as JSON, with per-block separators."""
    parts = []
    for i, item in enumerate(system):
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            rendered = item["text"]
        else:
            rendered = json.dumps(item, indent=2)
        parts.append(f"=== system[{i}] ===\n{rendered}")
    return "\n\n".join(parts)


def load(loader):
    """Called once at mitmproxy startup."""
    del loader  # unused
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


UNCAUGHT_RULE = "_uncaught-syspatch"


def request(flow):
    """mitmproxy request hook. Wraps _request so a bug here (an unexpected
    system shape, a regression in apply_patches) lands in the same
    content-addressed capture as a patch-application issue, instead of only
    flashing through mitmproxy's own log."""
    try:
        _request(flow)
    except Exception as exc:
        capture_uncaught(UNCAUGHT_RULE, exc, CAPTURE_DIR)
        raise


def _request(flow):
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
        bodies = [
            item
            for item in system
            if isinstance(item, dict)
            and item.get("type") == "text"
            and item.get("text", "").startswith(BODY_MARKER)
        ]
        if len(bodies) != 1:
            if not bodies and (is_auxiliary_system(system) or is_subagent_request(system)):
                # Expected, high-frequency (every subagent call): silent like
                # a patch-level match miss, not logged at info -- we are not
                # happy to see this every time, only if we go looking.
                logging.debug("non-interactive request: no prompt body to patch; ok")
            else:
                issue = Incident(LOCATOR_RULE, f"found-{len(bodies)}-prompt-bodies")
                report_issues(render_system_blocks(system), [issue], CAPTURE_DIR)
            return
        body = bodies[0]
        body["text"] = apply_patches(body["text"], PATCHES)
    else:
        raise AssertionError(("unexpected system type", type(system)))

    flow.request.set_content(json.dumps(request).encode())
