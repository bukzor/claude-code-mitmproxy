"""Restore plaintext thinking on Opus 4.7+ via two patches:

1. Strip `redact-thinking-2026-02-12` from the `anthropic-beta` header.
   Claude Code sends this beta unconditionally, which forces thinking
   redaction (empty text + opaque signature) on Opus 4.7+.
2. Inject `thinking.display=summarized` into the request body. Opus 4.7+
   defaults this to "omitted"; both patches are required.
"""
from __future__ import annotations

import json

from incidents import CAPTURE_DIR, capture_uncaught

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
    assert thinking.get("type") == "adaptive", ("unexpected thinking config", thinking)

    existing_display = thinking.get("display")
    assert existing_display in (None, "summarized"), (
        "unexpected thinking.display",
        existing_display,
    )

    if existing_display == "summarized":
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
        capture_uncaught(UNCAUGHT_RULE, exc, CAPTURE_DIR)
        raise
