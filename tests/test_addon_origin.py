"""The addons read the origin off the request they are already patching.

Library-level tests cover what the record says; these cover the wiring that
supplies it, which is the half a signature change can silently leave behind.
"""

from __future__ import annotations

import json

import pytest
from mitmproxy.test import tflow

from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_location
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import tool_patches
from claude_mitmproxy.addons import syspatch
from claude_mitmproxy.addons import toolpatch

BILLING_HEADER = "x-anthropic-billing-header: cc_version=2.1.248.abc; cc_entrypoint=cli;"


def request_flow(body: dict):
    flow = tflow.tflow()
    flow.request.set_content(json.dumps(body).encode())
    return flow


@pytest.fixture
def capture_dir(tmp_path, monkeypatch):
    """Incidents land in the test's own directory: the real CAPTURE_DIR is a
    triage queue a human works, and a test must never queue work.

    This bites only because the addons pass `incidents.CAPTURE_DIR` explicitly
    on every call. The library defaults bind it at import time, so a call that
    drops the argument writes to the live queue whatever this patches."""
    monkeypatch.setattr(incidents, "CAPTURE_DIR", tmp_path)
    return tmp_path


def test_toolpatch_records_the_requests_origin(capture_dir, monkeypatch):
    patch = tool_patches.ToolPatch("Bash", ("the accepted wording",), "the stub")
    monkeypatch.setattr(tool_patches, "load_tool_patches", lambda _: {"Bash": patch})

    flow = request_flow({
        "model": "claude-opus-5",
        "system": [{"type": "text", "text": BILLING_HEADER}],
        "tools": [{"name": "Bash", "description": "a drifted wording"}],
    })
    toolpatch.request(flow)

    (record_path,) = (capture_dir / "tooldesc-Bash").glob("*.json")
    record = json.loads(record_path.read_text())
    assert record["cc_version"] == "2.1.248.abc", record
    assert record["model"] == "claude-opus-5", record
    # the stub still goes out -- availability over freshness
    sent = json.loads(flow.request.get_content() or b"{}")
    assert sent["tools"][0]["description"] == "the stub", sent


def test_syspatch_records_the_requests_origin(capture_dir, tmp_path, monkeypatch):
    """Both loud paths in this addon: the per-patch miss and the aggregate
    `_strip-rate` tripwire, which fire from separate call sites."""
    rule_dir = tmp_path / "patches" / "a-patch"
    rule_dir.mkdir(parents=True)
    (rule_dir / "match.md").write_text("MATCHES")
    (rule_dir / "search.md").write_text("ABSENT")
    (rule_dir / "replace.md").write_text("")
    monkeypatch.setattr(prompt_patches, "PATCHES_DIR", tmp_path / "patches")

    flow = request_flow({
        "model": "claude-sonnet-5",
        "system": [
            {"type": "text", "text": BILLING_HEADER},
            {"type": "text", "text": prompt_location.BODY_MARKER + " that MATCHES"},
        ],
    })
    syspatch.request(flow)

    for rule in ("a-patch", prompt_patches.STRIP_RULE):
        (record_path,) = (capture_dir / rule).glob("*.json")
        record = json.loads(record_path.read_text())
        assert record["cc_version"] == "2.1.248.abc", (rule, record)
        assert record["model"] == "claude-sonnet-5", (rule, record)
