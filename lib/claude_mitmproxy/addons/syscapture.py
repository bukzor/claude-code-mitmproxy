"""mitmproxy addon: record every unique system-prompt body crossing the proxy.

Hooks only; `prompt_capture` does the writing and the dedup. Loaded before
`syspatch.py` (addon hooks run in load order), which is the whole reason this
is a separate addon rather than a branch inside that one -- bodies must be
recorded pristine, pre-patch.
"""

from __future__ import annotations

import json
import logging

from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_capture
from claude_mitmproxy import prompt_location

UNCAUGHT_RULE = "_uncaught-syscapture"


def request(flow):
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

    if not isinstance(request, dict):
        return

    system = request.get("system")
    if isinstance(system, str):
        bodies = [system] if prompt_location.BODY_MARKER in system else []
        subagent_body = None
    elif isinstance(system, list):
        bodies = [item["text"] for item in prompt_location.locate_prompt_bodies(system)]
        subagent_body = prompt_location.locate_subagent_body(system)
    else:
        return

    model = request.get("model", "unknown")
    cc_version = prompt_location.cc_version_of(system)
    for body in bodies:
        saved = prompt_capture.save_prompt(body, cc_version, model)
        if saved is not None:
            logging.info("captured new system prompt -> %s", saved)
    if subagent_body is not None:
        saved = prompt_capture.save_prompt(
            subagent_body, cc_version, model, prompt_capture.PROMPTS_DIR / "subagents"
        )
        if saved is not None:
            logging.info("captured new subagent prompt -> %s", saved)
