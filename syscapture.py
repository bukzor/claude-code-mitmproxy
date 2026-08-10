"""Capture each unique Claude Code system-prompt body crossing the proxy.

Loaded before syspatch.py (addon hooks run in load order), so bodies are
recorded pristine, pre-patch -- unlike traffic.jsonl/traffic.flow, which
record what was actually sent upstream. One pair of files per unique body
lands in log/prompt-captures/ (gitignored), keyed by v{cc_version}_{model}_
{digest}: {digest}.raw.md is the verbatim body, {digest}.md is its masked
sibling (incidents.normalize_body) -- the low-noise day-to-day diff target,
since the raw form carries per-session boilerplate (cwd, gitStatus, ...) that
swamps real prompt changes.

The digest in the name is of the raw body, while what makes a body "unique"
is its *masked* digest, so the same prompt re-seen across sessions and
restarts writes and logs exactly once. Two keys rather than one because a
mask edit moves every masked digest at once: names have to survive that,
dedup has to follow it (design/040-design.kb/content-addressed-capture.md).

Promote a capture's .raw.md into system-prompts.kb/ per that collection's
CLAUDE.md -- check_patches.py needs the pristine, unmasked text.

Subagent bodies (locate_subagent_body: Explore, Plan, claude-code-guide,
...) are captured for the same visibility but land in the subagents/
subdirectory: they are never patched, so they must not sit where the
promotion duty (and survey_captures.py) enumerates promotion candidates.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import incidents
import syspatch
import templates

PROMPTS_DIR = Path(__file__).parent / "log" / "prompt-captures"
UNCAUGHT_RULE = "_uncaught-syscapture"

# cc_version rides in the billing-header block, not the prompt body itself.
CC_VERSION_RE = re.compile(r"\bcc_version=([^;\s\"]+)")

# {directory: (mask set the digests were taken under, those digests)}. Held per
# process rather than on disk: the .raw.md files are the only durable input, so
# a rebuild is always available and can never disagree with them.
_CAPTURED: dict[Path, tuple[tuple[templates.Template, ...], set[str]]] = {}


def cc_version_of(system) -> str:
    if isinstance(system, list) and system:
        first = system[0]
        if isinstance(first, dict) and isinstance(first.get("text"), str):
            m = CC_VERSION_RE.search(first["text"])
            if m is not None:
                return m.group(1)
    return "unknown"


def load_masked_digests(
    directory: Path, masks: tuple[templates.Template, ...]
) -> set[str]:
    """The masked digest of every capture already in directory -- the question
    dedup asks, since two sessions that ran the same prompt differently have to
    capture once between them. The returned set is the live cache: a caller
    that writes a new capture adds to it.

    Rebuilt from the raw bodies whenever `masks` differs from the set the
    cached answer was taken under, which is why a masks.d/ edit needs no
    follow-up command -- the mask set is re-read per request anyway, and a
    changed one cannot compare equal to the old one. The same pass rewrites any
    masked sibling the new masks change, since that file is derived too and
    nothing else would notice it had gone stale."""
    cached = _CAPTURED.get(directory)
    if cached is not None and cached[0] == masks:
        return cached[1]
    digests: set[str] = set()
    for raw in sorted(directory.glob("*.raw.md")):
        masked = templates.apply_masks(raw.read_text(), masks)
        digests.add(incidents.digest_of(masked))
        sibling = directory / f"{raw.name.removesuffix('.raw.md')}.md"
        if not sibling.exists() or sibling.read_text() != masked:
            sibling.write_text(masked)
    _CAPTURED[directory] = (masks, digests)
    return digests


def save_prompt(
    body: str, cc_version: str, model: str, directory: Path = PROMPTS_DIR
) -> Path | None:
    """Write the raw body plus its masked sibling once; return the raw path
    when freshly written, None when this content was already captured under any
    name. Named by the raw body's digest and deduplicated by the masked one, so
    a version bump that leaves the prompt text unchanged captures nothing while
    a mask edit renames nothing. cc_version and model in the name are
    provenance. Dedup is per-directory: main and subagent captures are separate
    namespaces."""
    directory.mkdir(parents=True, exist_ok=True)
    masks = incidents.masks()
    masked = templates.apply_masks(body, masks)
    captured = load_masked_digests(directory, masks)
    masked_digest = incidents.digest_of(masked)
    if masked_digest in captured:
        return None
    base_name = f"v{cc_version}_{model}_{incidents.digest_of(body)}"
    raw_path = directory / f"{base_name}.raw.md"
    raw_path.write_text(body)
    (directory / f"{base_name}.md").write_text(masked)
    captured.add(masked_digest)
    return raw_path


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
        bodies = [system] if syspatch.BODY_MARKER in system else []
        subagent_body = None
    elif isinstance(system, list):
        bodies = [item["text"] for item in syspatch.locate_prompt_bodies(system)]
        subagent_body = syspatch.locate_subagent_body(system)
    else:
        return

    model = request.get("model", "unknown")
    cc_version = cc_version_of(system)
    for body in bodies:
        saved = save_prompt(body, cc_version, model)
        if saved is not None:
            logging.info("captured new system prompt -> %s", saved)
    if subagent_body is not None:
        saved = save_prompt(subagent_body, cc_version, model, PROMPTS_DIR / "subagents")
        if saved is not None:
            logging.info("captured new subagent prompt -> %s", saved)
