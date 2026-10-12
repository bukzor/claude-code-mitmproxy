"""thinkpatch rewrites the thinking config of the requests Claude Code sends.

Claude Code picks the `display` it asks for: unset, `"omitted"`, or (v2.1.327)
`"updates"` under the `thinking-display-updates-*` beta -- each redacts, and
must land as plain `"summarized"`. `"summarized"` and `"highlights"` already
return thinking text and pass through. The updates beta stays: it enables the
value rather than forcing redaction (CLAUDE.kb/thinking-display.md).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from claude_mitmproxy.addons import thinkpatch

UPDATES_BETA = "thinking-display-updates-2026-08-18"


def make_flow(thinking: dict | None, betas: str = "") -> SimpleNamespace:
    body = {"model": "claude-opus-5-5"}
    if thinking is not None:
        body["thinking"] = thinking
    content = json.dumps(body).encode()
    request = SimpleNamespace(
        headers={"anthropic-beta": betas} if betas else {},
        get_content=lambda: request.content,
        set_content=lambda new: setattr(request, "content", new),
        content=content,
    )
    return SimpleNamespace(request=request)


def patched_thinking(flow) -> dict:
    thinkpatch._patch_anthropic_beta(flow)
    thinkpatch._patch_thinking_body(flow)
    return json.loads(flow.request.content)["thinking"]


@pytest.mark.parametrize("display", [None, "omitted", "updates"])
def test_redacting_display_becomes_summarized(display):
    config = {"type": "adaptive"}
    if display:
        config["display"] = display
    assert patched_thinking(make_flow(config)) == {
        "type": "adaptive",
        "display": "summarized",
    }


@pytest.mark.parametrize("display", ["summarized", "highlights"])
def test_visible_display_is_left_alone(display):
    flow = make_flow({"type": "adaptive", "display": display})
    before = flow.request.content
    patched_thinking(flow)
    assert flow.request.content == before


def test_only_the_redact_beta_is_stripped():
    flow = make_flow(
        {"type": "adaptive", "display": "updates"},
        betas=f"a-beta,{UPDATES_BETA},{thinkpatch.REDACT_BETA},b-beta",
    )
    patched_thinking(flow)
    assert flow.request.headers["anthropic-beta"] == f"a-beta,{UPDATES_BETA},b-beta"


def test_unknown_display_is_still_loud():
    with pytest.raises(AssertionError):
        patched_thinking(make_flow({"type": "adaptive", "display": "bogus"}))
