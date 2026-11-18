"""Restore plaintext thinking on Opus 4.7+ via two patches:

1. Strip `redact-thinking-2026-02-12` from the `anthropic-beta` header.
   Through some version before v2.1.327, Claude Code sent this beta
   unconditionally, forcing thinking redaction (empty text + opaque
   signature) on Opus 4.7+. v2.1.327 no longer sends it.
2. Inject `thinking.display=summarized` into the request body. Opus 4.7+
   defaults this to "omitted"; v2.1.327 Claude Code sends "updates"
   (empty thinking plus a token estimate). Both are overwritten.
"""
from __future__ import annotations

import json

from claude_mitmproxy import incidents

REDACT_BETA = "redact-thinking-2026-02-12"
UNCAUGHT_RULE = "_uncaught-thinkpatch"


def _patch_anthropic_beta(flow) -> None:
    raw = flow.request.headers.get("anthropic-beta")
    if not raw:
        return
    parts = [p.strip() for p in raw.split(",")]
    if REDACT_BETA not in parts:
        return
    kept = [p for p in parts if p != REDACT_BETA]
    flow.request.headers["anthropic-beta"] = ",".join(kept)


def _patch_thinking_body(flow) -> None:
    content_bytes = flow.request.get_content()
    if not content_bytes:
        return

    try:
        body = json.loads(content_bytes)
    except json.JSONDecodeError:
        return

    thinking = body.get("thinking")
    if thinking is None:
        return

    assert isinstance(thinking, dict), ("unexpected thinking type", type(thinking), thinking)
    thinking_type = thinking.get("type")
    if thinking_type in ("disabled", "enabled"):
        # Auxiliary CLI calls (session-title generation, ...) send
        # `{"type": "disabled"}`; subagent requests using classic
        # (non-adaptive) reasoning send `{"type": "enabled", "budget_tokens":
        # N}` -- a config shape with no "display" field to set in the first
        # place. Only the interactive-agent request uses "adaptive".
        return
    assert thinking_type == "adaptive", ("unexpected thinking config", thinking)

    existing_display = thinking.get("display")
    assert existing_display in (None, "omitted", "updates", "summarized", "highlights"), (
        "unexpected thinking.display",
        existing_display,
    )

    if existing_display in ("summarized", "highlights"):
        # Both already return thinking text; see CLAUDE.kb/thinking-display.md.
        return

    thinking["display"] = "summarized"
    flow.request.set_content(json.dumps(body).encode())


def request(flow):
    from mitmproxy import http

    assert isinstance(flow, http.HTTPFlow)
    try:
        _patch_anthropic_beta(flow)
        _patch_thinking_body(flow)
    except Exception as exc:
        incidents.capture_uncaught(UNCAUGHT_RULE, exc, incidents.CAPTURE_DIR)
        raise
