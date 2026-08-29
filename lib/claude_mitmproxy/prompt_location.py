"""Where the system prompt sits in a Claude Code request, and which requests
have one at all.

Pure wire-protocol knowledge: no patching, no capture, no incidents -- given a
request's `system` field, say which block is the interactive prompt body. It
drifts on Anthropic's schedule rather than ours, which is why it is its own
module: `prompt_patches` and `prompt_capture` both need the answer, and neither
should be the place a reader goes looking for it.

`CLAUDE.kb/system-prompt-loci.md` records how the surface was mapped;
`CLAUDE.kb/subagent-request-shape.md` covers the subagent variant.
"""

from __future__ import annotations

import json
import re

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
    "You are naming a coding session",  # session-title generation, v2.1.234
    "You are an assistant for performing a web search tool use",
    "You are a security monitor for autonomous AI coding agents",
    # auto-mode configuration proposal (auto-mode setup flow, v2.1.232)
    "You transform a mechanically-gathered recon block",
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

# cc_version rides in the billing-header block, not the prompt body itself.
CC_VERSION_RE = re.compile(r"\bcc_version=([^;\s\"]+)")


def cc_version_of(system) -> str:
    """The Claude Code build that sent this request, or "unknown" when the
    billing header is absent or unparseable. Accepts any `system` -- a
    caller holding a request field shouldn't have to narrow it first."""
    if isinstance(system, list) and system:
        first = system[0]
        if isinstance(first, dict) and isinstance(first.get("text"), str):
            m = CC_VERSION_RE.search(first["text"])
            if m is not None:
                return m.group(1)
    return "unknown"


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
