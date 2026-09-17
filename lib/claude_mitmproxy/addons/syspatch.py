"""mitmproxy addon: rewrite Claude-Code-authored instruction text in flight.

Two loci, one addon: the system prompt body, and the `role: "system"` entries
in `messages[]` that carry mid-conversation instructions. Same job, same
incident rule, same capture dir, and one `json.loads` of the body for both.

Hooks only. Finding the prompt body is `prompt_location`, rewriting it is
`prompt_patches`, walking the system messages is `message_patches`, and all
three are importable without mitmproxy -- which is how the offline checks and
the tests run the same code this addon does.
"""

from __future__ import annotations

import json
import logging

from claude_mitmproxy import gc_patch_failures
from claude_mitmproxy import incidents
from claude_mitmproxy import message_patches
from claude_mitmproxy import prompt_location
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates

UNCAUGHT_RULE = "_uncaught-syspatch"


def load(loader):
    """Called once at mitmproxy startup. Patches are re-read from disk on
    every request (see _request) so editing `*-patches.d/` takes effect
    immediately -- this hook only logs what's configured at startup.

    Masks are re-read the same way, but compiling them here too is not
    redundant: a malformed one takes the proxy down at startup rather than
    at hash time. Editing `masks.d/` needs no restart and no follow-up: no
    stored name depends on the mask set, and what does re-derives itself.

    It also sweeps `log/patch-failures/`, which has nothing to do with
    patching a system prompt -- it is here because a load hook is the only
    once-per-proxy occasion this repo has, and because that store is already
    this addon's heaviest dependency."""
    del loader  # unused
    patches = rule_templates.load_rules(prompt_patches.PATCHES_DIR)
    logging.info("loaded %d system prompt patches", len(patches))
    for patch in patches:
        if patch.upstream_removed:
            label = "upstream-removed"
        elif patch.search:
            label = "match+search"
        else:
            label = "match-only"
        logging.info("  %s (%s)", patch.name, label)
    message_rules = rule_templates.load_rules(message_patches.PATCHES_DIR)
    logging.info("loaded %d system message patches", len(message_rules))
    for patch in message_rules:
        logging.info("  %s", patch.name)
    logging.info("loaded %d capture-digest masks", len(incidents.masks()))
    gc_patch_failures.sweep_at_startup()


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
    patches = rule_templates.load_rules(prompt_patches.PATCHES_DIR)
    origin = incidents.Origin(
        prompt_location.cc_version_of(system), request.get("model", "unknown")
    )

    _patch_prompt(request, system, patches, origin)

    messages = request.get("messages")
    if isinstance(messages, list):
        message_patches.patch_system_messages(
            messages,
            rule_templates.load_rules(message_patches.PATCHES_DIR),
            incidents.CAPTURE_DIR,
            origin,
        )

    flow.request.set_content(json.dumps(request).encode())


def _patch_prompt(request, system, patches, origin):
    """Rewrite the prompt body in `request`, in place.

    A request that carries no locatable body -- a subagent call, an auxiliary
    CLI shape -- returns having changed nothing, which is not the end of the
    request: the `role: "system"` messages are a separate locus and are
    patched either way."""
    if isinstance(system, str):
        patched = prompt_patches.apply_patches(system, patches, incidents.CAPTURE_DIR, origin)
        request["system"] = patched
        if prompt_location.BODY_MARKER in system:
            prompt_patches.check_strip_floor(
                system, patched, patches, incidents.CAPTURE_DIR, origin
            )
    elif isinstance(system, list):
        bodies = prompt_location.locate_prompt_bodies(system)
        if len(bodies) != 1:
            if not bodies and (
                prompt_location.is_auxiliary_system(system)
                or prompt_location.is_subagent_request(system)
            ):
                # Expected, high-frequency (every subagent call): silent like
                # a patch-level match miss, not logged at info -- we are not
                # happy to see this every time, only if we go looking.
                logging.debug("non-interactive request: no prompt body to patch; ok")
            else:
                kind = f"found-{len(bodies)}-prompt-bodies"
                issue = incidents.Incident(prompt_location.LOCATOR_RULE, kind)
                incidents.report_issues(
                    prompt_location.render_system_blocks(system),
                    [issue],
                    incidents.CAPTURE_DIR,
                    origin,
                )
            return
        body = bodies[0]
        original = body["text"]
        patched = prompt_patches.apply_patches(original, patches, incidents.CAPTURE_DIR, origin)
        body["text"] = patched
        prompt_patches.check_strip_floor(
            original, patched, patches, incidents.CAPTURE_DIR, origin
        )
    else:
        raise AssertionError(("unexpected system type", type(system)))
