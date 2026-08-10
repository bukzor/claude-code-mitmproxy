"""Apply modular patches to the Claude Code system prompt via mitmproxy."""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path

import incidents
import shapes
import templates


def apply_patches(
    text: str,
    patches: tuple[templates.Rule, ...],
    capture_dir: Path | None = incidents.CAPTURE_DIR,
) -> str:
    """`templates.apply_rules` plus this project's loudness policy: a patch
    that proved itself in scope and then failed to find its target is an
    incident, captured content-addressed so it warns exactly once. Which
    misses are worth a warning is the caller's call, not the engine's --
    masks run the same templates and are never loud."""
    patched, misses = templates.apply_rules(text, patches)
    if misses:
        issues = [incidents.Incident(*miss) for miss in misses]
        incidents.report_issues(text, issues, capture_dir)
    return patched


# --- aggregate strip-rate tripwire ---

KB_DIR = Path(__file__).parent / "system-prompts.kb"
STRIP_RULE = "_strip-rate"


def _fixture_version(path: Path) -> tuple[int, ...]:
    release = path.stem.removeprefix("v").split("-")[0]
    return tuple(int(part) for part in release.split("."))


@functools.lru_cache(maxsize=1)
def strip_floors(patches: tuple[templates.Rule, ...]) -> dict[str, int]:
    """Minimum bytes the patch set must strip from a live body, per prompt
    shape: half of what it strips from the newest promoted fixture of that
    shape (newest by version, then size, so a full capture beats a `-scope`
    partial). Halving absorbs session-optional content a fixture carries
    but a minimal live session doesn't (gitStatus, additional dirs); an
    upstream rewrite leaves only the shape-independent patches firing, far
    below any floor. Cached per patch set -- Rule stores templates as
    strings, so value-equal loads share one entry; a fixture promoted
    mid-process is picked up by `touch reload.py`, which rebuilds this
    module and the cache with it."""
    newest: dict[str, tuple[tuple, str]] = {}
    for path in KB_DIR.glob("v*.md"):
        text = path.read_text()
        shape = shapes.shape_of(text)
        if shape.startswith("?"):
            continue
        key = (_fixture_version(path), len(text))
        if shape not in newest or key > newest[shape][0]:
            newest[shape] = (key, text)
    assert newest, (KB_DIR, "no classifiable fixtures")
    return {
        shape: (len(text) - len(apply_patches(text, patches, capture_dir=None))) // 2
        for shape, (_, text) in newest.items()
    }


def check_strip_floor(
    original: str,
    patched: str,
    patches: tuple[templates.Rule, ...],
    capture_dir: Path | None,
) -> None:
    """The aggregate check no per-patch rule can provide: an upstream
    rewrite sends every shape-scoped patch silently out of scope at once,
    and per-patch loudness reports that as nothing (2026-08-04 incident,
    see session.kb). A patched main body must strip at least its shape's
    floor; a body matching no known shape is the same alarm one step
    earlier."""
    shape = shapes.shape_of(original)
    floor = strip_floors(patches).get(shape)
    stripped = len(original) - len(patched)
    if floor is None:
        issue = incidents.Incident(STRIP_RULE, f"unknown-shape-{shape}")
    elif stripped < floor:
        issue = incidents.Incident(
            STRIP_RULE, f"low-strip-{shape}-{stripped}B-floor-{floor}B"
        )
    else:
        return
    incidents.report_issues(original, [issue], capture_dir)


# --- mitmproxy addon ---

PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()

# Opening text that identifies the main prompt body among `system` blocks.
BODY_MARKER = "\nYou are an interactive agent"
# Incident rule for a `system` list without exactly one such block.
# Underscore-prefixed, like _bodies, so it can't collide with a patch name.
LOCATOR_RULE = "_locate-system-prompt"

# Auxiliary CLI requests (session-title generation, web-search helper, ...)
# legitimately carry no interactive prompt body. Recognized by shape, not by
# full prompt text: every block must be a billing header, a bare identity
# line, a known task prompt, or a trailing session-context block. A drifted
# interactive prompt still captures -- its body block matches none of these.
IDENTITY_LINES = (
    "You are Claude Code, Anthropic's official CLI for Claude.",
    # sdk-cli entrypoint (observed on session-title generation)
    "You are a Claude agent, built on Anthropic's Claude Agent SDK.",
)
AUX_TASK_PREFIXES = (
    "Generate a concise, sentence-case title",
    "Generate a short kebab-case name",  # session-title generation, reworded
    "You are an assistant for performing a web search tool use",
    "You are a security monitor for autonomous AI coding agents",
    # phone-notification classifier (PushNotification tool)
    "A user kicked off a Claude Code agent to do a coding task and walked away",
)
# A trailing per-session context block (user identity) may follow the task
# prompt -- seen on the auto-mode security-monitor request. It leads with
# blank lines, so match after lstrip; being session-volatile it never carries
# a prompt body of its own.
AUX_TRAILER_PREFIXES = ("## Session Context",)

# Subagent requests (Task-tool invocations) carry a per-agent-type prompt
# template that never uses BODY_MARKER either, but unlike the auxiliary CLI
# shapes above, the template body itself varies arbitrarily by agent type
# (claude-code-guide, Explore, general-purpose, ...) -- too open-ended to
# enumerate block-by-block. Recognize the request instead, via the billing
# header's own subagent flag.
SUBAGENT_MARKER = "cc_is_subagent=true"


def locate_prompt_bodies(system: list) -> list[dict]:
    """The text blocks carrying an interactive prompt body (BODY_MARKER).
    Exactly one is expected in an interactive request; callers handle 0/N."""
    return [
        item
        for item in system
        if isinstance(item, dict)
        and item.get("type") == "text"
        and item.get("text", "").startswith(BODY_MARKER)
    ]


def is_auxiliary_system(system: list) -> bool:
    """True when every system block belongs to a recognized non-interactive
    request shape, so a missing prompt body is expected, not an incident."""
    return bool(system) and all(_is_auxiliary_block(item) for item in system)


def is_subagent_request(system: list) -> bool:
    """True when the billing-header block marks this a subagent request.
    Most agent types' prompt body is agent-type-specific and never
    carries BODY_MARKER; the general-purpose/default agent type is an
    exception -- it resends the interactive body verbatim, so it takes
    the ordinary patched/captured path instead of this branch."""
    if not system:
        return False
    first = system[0]
    return (
        isinstance(first, dict)
        and isinstance(first.get("text"), str)
        and first["text"].startswith("x-anthropic-billing-header:")
        and SUBAGENT_MARKER in first["text"]
    )


def locate_subagent_body(system: list) -> str | None:
    """The agent-type-specific prompt text for a specialized subagent
    request (Explore, Plan, claude-code-guide, ...) -- every block after
    the billing header, joined. None when this isn't a bodyless subagent
    request: the default/general-purpose agent type resends the
    interactive body, which `locate_prompt_bodies` already finds, so
    there's nothing left for this function to do."""
    if not is_subagent_request(system) or locate_prompt_bodies(system):
        return None
    parts = [
        item["text"]
        for item in system[1:]
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    return "\n\n".join(parts) if parts else None


def _is_auxiliary_block(item) -> bool:
    if not (isinstance(item, dict) and isinstance(item.get("text"), str)):
        return False
    else:
        text = item["text"]
        return (
            text.startswith("x-anthropic-billing-header:")
            or text.strip() in IDENTITY_LINES
            or text.startswith(AUX_TASK_PREFIXES)
            or text.lstrip().startswith(AUX_TRAILER_PREFIXES)
        )


def render_system_blocks(system: list) -> str:
    """Flatten a content-blocks `system` list into one capture body: text
    blocks verbatim (so masking still neutralizes session-volatile
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
    """Called once at mitmproxy startup. Patches are re-read from disk on
    every request (see _request) so editing `*-patches.d/` takes effect
    immediately -- this hook only logs what's configured at startup.

    Masks are re-read the same way, but compiling them here too is not
    redundant: a malformed one takes the proxy down at startup rather than
    at hash time. Editing `masks.d/` needs no restart and no follow-up: no
    stored name depends on the mask set, and what does re-derives itself."""
    del loader  # unused
    patches = templates.load_rules(PATCHES_DIR)
    logging.info("loaded %d system prompt patches", len(patches))
    for patch in patches:
        if patch.upstream_removed:
            label = "upstream-removed"
        elif patch.search:
            label = "match+search"
        else:
            label = "match-only"
        logging.info("  %s (%s)", patch.name, label)
    logging.info("loaded %d capture-digest masks", len(incidents.masks()))


UNCAUGHT_RULE = "_uncaught-syspatch"


def request(flow):
    """mitmproxy request hook. Wraps _request so a bug here (an unexpected
    system shape, a regression in apply_patches) lands in the same
    content-addressed capture as a patch-application issue, instead of only
    flashing through mitmproxy's own log."""
    try:
        _request(flow)
    except Exception as exc:
        incidents.capture_uncaught(UNCAUGHT_RULE, exc, incidents.CAPTURE_DIR)
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

    # Re-read per request: editing `*-patches.d/` takes effect without a
    # restart (`CLAUDE.kb/patches-reread-per-request.md`).
    patches = templates.load_rules(PATCHES_DIR)

    if isinstance(system, str):
        patched = apply_patches(system, patches)
        request["system"] = patched
        if BODY_MARKER in system:
            check_strip_floor(system, patched, patches, incidents.CAPTURE_DIR)
    elif isinstance(system, list):
        bodies = locate_prompt_bodies(system)
        if len(bodies) != 1:
            if not bodies and (is_auxiliary_system(system) or is_subagent_request(system)):
                # Expected, high-frequency (every subagent call): silent like
                # a patch-level match miss, not logged at info -- we are not
                # happy to see this every time, only if we go looking.
                logging.debug("non-interactive request: no prompt body to patch; ok")
            else:
                kind = f"found-{len(bodies)}-prompt-bodies"
                issue = incidents.Incident(LOCATOR_RULE, kind)
                incidents.report_issues(
                    render_system_blocks(system), [issue], incidents.CAPTURE_DIR
                )
            return
        body = bodies[0]
        original = body["text"]
        patched = apply_patches(original, patches)
        body["text"] = patched
        check_strip_floor(original, patched, patches, incidents.CAPTURE_DIR)
    else:
        raise AssertionError(("unexpected system type", type(system)))

    flow.request.set_content(json.dumps(request).encode())
