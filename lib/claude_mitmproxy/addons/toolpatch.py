"""mitmproxy addon: replace built-in tool descriptions with slim stubs.

Hooks only; `tool_patches` loads the patch directories and does the swap.
Patch format and triage workflow:
~/.claude/tool-description-patches.d/README.md.
"""

from __future__ import annotations

import json
import logging

from claude_mitmproxy import incidents
from claude_mitmproxy import tool_patches

UNCAUGHT_RULE = "_uncaught-toolpatch"


def load(loader):
    """Called once at mitmproxy startup. Patches are re-read from disk on
    every request (see _request) so editing `*-patches.d/` takes effect
    immediately -- this hook only logs what's configured at startup."""
    del loader  # unused
    patches = tool_patches.load_tool_patches(tool_patches.PATCHES_DIR)
    logging.info("loaded %d tool description patches", len(patches))
    for patch in patches.values():
        logging.info(
            "  %s (%d upstream variants -> %d chars)",
            patch.name,
            len(patch.upstreams),
            len(patch.replacement),
        )


def request(flow):
    """mitmproxy request hook. Wraps _request so a bug here lands in the same
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

    if not isinstance(request, dict):
        return
    tools = request.get("tools")
    if not isinstance(tools, list):
        return

    tool_patches.apply_tool_patches(
        tools, tool_patches.load_tool_patches(tool_patches.PATCHES_DIR)
    )
    flow.request.set_content(json.dumps(request).encode())
