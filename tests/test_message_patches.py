"""The live `system-message.d/` rules against the bodies Claude Code sends.

The rules are loaded from `message_patches.PATCHES_DIR`, not from a fixture
directory: what is worth knowing is that the operator's real config kills the
real steer. The upstream bodies are carried here verbatim instead, since this
locus has no captured fixtures (`system-message.d/README.md`).
"""

from __future__ import annotations

import pytest

from claude_mitmproxy import incidents
from claude_mitmproxy import message_patches
from claude_mitmproxy import rule_templates

RULES = rule_templates.load_rules(message_patches.PATCHES_DIR)

# The two arms of the `tengu_cozy_teapot` gate, verbatim as served.
STRICT = "Do your work through the Bash tool wherever it can accomplish the job: read files with cat, head, or sed -n, search with grep and find, and make file changes with sed, heredocs, or short scripts, rather than using the dedicated Read, Edit, or Write tools. Fall back to a dedicated tool only when Bash genuinely cannot do the job."
RELAXED = "You can do much of your work through the Bash tool when it is the simpler route: read files with cat, head, or sed -n, search with grep and find, and make small, mechanical file changes with sed, heredocs, or short scripts instead of the dedicated Read, Edit, or Write tools. The choice is yours: prefer Edit or Write when a shell edit would be fragile, such as exact or multi-line replacements, or sed/awk flags that differ between GNU and BSD/macOS."

# The message the steer rides in on: a plan-mode transition, then the heading.
ENVELOPE = (
    "## Exited Plan Mode\n\n"
    "You have exited plan mode. You can now make edits, run tools, and take actions.\n\n"
    "While auto mode is active:\n\n"
)
# The heading survives -- it is part of the match, and it is still true.
PATCHED = ENVELOPE[:-1]

# A tool result quoting the rule files themselves, as observed on the wire
# 2026-09-17. The heading arrives here too, followed by `2\t` rather than a
# blank line, and the steer body sits a tool result further down.
QUOTED = (
    'Called the Read tool with the following input: {"file_path":"match.md"}\n'
    "Result of calling the Read tool:\n"
    "1\tWhile auto mode is active:\n"
    "2\t\n"
    "\n"
    'Called the Read tool with the following input: {"file_path":"strict.md"}\n'
    "Result of calling the Read tool:\n"
    "1\t" + STRICT + "\n"
    "2\t\n"
)


@pytest.fixture
def reported(monkeypatch):
    """Every incident the patches would file, collected instead of filed."""
    calls: list[tuple[str, list]] = []
    monkeypatch.setattr(
        incidents,
        "report_issues",
        lambda text, issues, capture_dir, origin: calls.append((text, issues)),
    )
    return calls


def test_strict_arm_deleted(reported):
    messages = [{"role": "system", "content": ENVELOPE + STRICT}]
    changed = message_patches.patch_system_messages(messages, RULES, capture_dir=None)
    assert changed
    assert messages[0]["content"] == PATCHED
    assert reported == []


def test_relaxed_arm_deleted(reported):
    messages = [{"role": "system", "content": ENVELOPE + RELAXED}]
    changed = message_patches.patch_system_messages(messages, RULES, capture_dir=None)
    assert changed
    assert messages[0]["content"] == PATCHED
    assert reported == []


def test_quoted_rule_files_untouched(reported):
    """The regression that matters most: a heading-anchored match would delete
    the steer out of a transcript the reader is looking at."""
    messages = [{"role": "system", "content": QUOTED}]
    changed = message_patches.patch_system_messages(messages, RULES, capture_dir=None)
    assert not changed
    assert messages[0]["content"] == QUOTED
    assert reported == []


def test_block_content_shape(reported):
    messages = [
        {"role": "system", "content": [{"type": "text", "text": ENVELOPE + STRICT}]}
    ]
    changed = message_patches.patch_system_messages(messages, RULES, capture_dir=None)
    assert changed
    assert messages[0]["content"] == [{"type": "text", "text": PATCHED}]
    assert reported == []


def test_non_system_roles_untouched(reported):
    messages = [{"role": "user", "content": ENVELOPE + STRICT}]
    changed = message_patches.patch_system_messages(messages, RULES, capture_dir=None)
    assert not changed
    assert messages[0]["content"] == ENVELOPE + STRICT
    assert reported == []
