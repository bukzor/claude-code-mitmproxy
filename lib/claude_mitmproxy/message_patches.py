"""Apply the same patch dialect to a third locus: the text of `messages[]`
entries whose role is `system`.

Claude Code delivers mid-conversation instructions there -- plan-mode
transitions, permission-mode notices, the auto-mode bash-first steer. The one
non-obvious fact about the locus: unlike `request.system`, that text is
interleaved with the conversation's own tool results, so a `role: "system"`
message can carry a verbatim copy of anything the session has read --
including the rules of this very directory. A rule anchored on too little
matches its own quotation and deletes it out of the transcript.

Rule dialect and that collision, worked through:
`~/.config/claude-mitmproxy/system-message.d/README.md`.

The message-walk half of `addons/syspatch.py`, minus every mitmproxy concept:
messages in, mutated in place, incidents filed by `prompt_patches` on the way.
"""

from __future__ import annotations

from pathlib import Path

from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates


def patch_system_messages(
    messages: list,
    patches: tuple[rule_templates.Rule, ...],
    capture_dir: Path | None = incidents.CAPTURE_DIR,
    origin: incidents.Origin = incidents.Origin(),
) -> bool:
    """Mutate `messages` in place, rewriting the text of every `system` entry,
    and report whether anything changed -- the caller's cue that the request
    body must be re-serialized even when the prompt itself was untouched.

    Both content shapes the API accepts are walked: a bare string, and a list
    of blocks. Anything else -- another role, a non-text block, a tool_result
    -- passes through untouched; absence of our text is not drift."""
    changed = False
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "system":
            continue
        content = message.get("content")
        if isinstance(content, str):
            patched = prompt_patches.apply_patches(content, patches, capture_dir, origin)
            if patched != content:
                message["content"] = patched
                changed = True
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "text":
                    continue
                text = block.get("text")
                if not isinstance(text, str):
                    continue
                patched = prompt_patches.apply_patches(text, patches, capture_dir, origin)
                if patched != text:
                    block["text"] = patched
                    changed = True
    return changed


# Re-read per request by the addon, so editing a rule takes effect without a
# restart (`CLAUDE.kb/patches-reread-per-request.md`). Under `~`, not in-repo:
# these encode one operator's preferences (`design/010-mission.kb/`).
PATCHES_DIR = Path("~/.config/claude-mitmproxy/system-message.d").expanduser()
