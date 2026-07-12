"""Capture each unique Claude Code system-prompt body crossing the proxy.

Loaded before syspatch.py (addon hooks run in load order), so bodies are
recorded pristine, pre-patch -- unlike traffic.jsonl/traffic.flow, which
record what was actually sent upstream. One pair of files per unique body
lands in prompt-captures/ (gitignored), keyed by v{cc_version}_{model}_{digest}:
{digest}.raw.md is the verbatim body, {digest}.md is its hash-normalized
sibling (incidents.normalize_body) -- the low-noise day-to-day diff target,
since the raw form carries per-session boilerplate (cwd, gitStatus, ...) that
swamps real prompt changes. digest is incidents.content_hash, so the same
prompt re-seen across sessions and restarts writes and logs exactly once.
Promote a capture's .raw.md into system-prompts.kb/ per that collection's
CLAUDE.md -- check_patches.py needs the pristine, unmasked text.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from incidents import CAPTURE_DIR, capture_uncaught, content_hash, normalize_body
from syspatch import BODY_MARKER, locate_prompt_bodies

PROMPTS_DIR = Path(__file__).parent / "prompt-captures"
UNCAUGHT_RULE = "_uncaught-syscapture"

# cc_version rides in the billing-header block, not the prompt body itself.
CC_VERSION_RE = re.compile(r"\bcc_version=([^;\s\"]+)")


def cc_version_of(system) -> str:
    if isinstance(system, list) and system:
        first = system[0]
        if isinstance(first, dict) and isinstance(first.get("text"), str):
            m = CC_VERSION_RE.search(first["text"])
            if m is not None:
                return m.group(1)
    return "unknown"


def save_prompt(body: str, cc_version: str, model: str) -> Path | None:
    """Write the raw body plus its normalized sibling once, keyed by
    content_hash; return the raw path when freshly written, None when this
    content was already captured under any name (the digest is the key --
    cc_version/model prefixes are provenance, so a version bump that leaves
    the prompt text unchanged captures nothing)."""
    digest = content_hash(body)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    if next(PROMPTS_DIR.glob(f"*_{digest}.raw.md"), None) is not None:
        return None
    base_name = f"v{cc_version}_{model}_{digest}"
    raw_path = PROMPTS_DIR / f"{base_name}.raw.md"
    raw_path.write_text(body)
    (PROMPTS_DIR / f"{base_name}.md").write_text(normalize_body(body))
    return raw_path


def request(flow):
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

    if not isinstance(request, dict):
        return

    system = request.get("system")
    if isinstance(system, str):
        bodies = [system] if BODY_MARKER in system else []
    elif isinstance(system, list):
        bodies = [item["text"] for item in locate_prompt_bodies(system)]
    else:
        return

    model = request.get("model", "unknown")
    cc_version = cc_version_of(system)
    for body in bodies:
        saved = save_prompt(body, cc_version, model)
        if saved is not None:
            logging.info("captured new system prompt -> %s", saved)
