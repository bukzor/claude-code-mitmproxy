"""The bodies every check reads, resolved through the module that writes them.

Nothing here resolves a path against the cwd. These same loaders serve the
hand-run commands and the `monitoring/` suite, so a check run from another
repo's session reads exactly what a run from this checkout reads -- and the
two halves of a check cannot disagree about which bodies they examined.
"""

from __future__ import annotations

from pathlib import Path

from claude_mitmproxy import prompt_capture
from claude_mitmproxy import prompt_location
from claude_mitmproxy import prompt_patches


def fixtures() -> dict[Path, str]:
    """The promoted fixtures, newline-terminated: a template ending "\\n" needs
    end-of-body to read as a line boundary, the same normalization
    `apply_masks` does before matching. Committed, so these are always here."""
    paths = sorted(p for p in prompt_patches.KB_DIR.glob("*.md") if p.name != "CLAUDE.md")
    assert paths, prompt_patches.KB_DIR
    texts = {p: p.read_text() for p in paths}
    return {p: t if t.endswith("\n") else t + "\n" for p, t in texts.items()}


def current_fixtures() -> list[Path]:
    """Every full fixture at the highest promoted release, name-sorted.

    Plural because upstream serves several bodies at one release -- shapes it
    picks per model, and copies of one shape while it reworks the text -- and
    a patch that misses on any of them misses in production. Validating one of
    them and calling it "the current prompt" is how half of what ships goes
    unchecked while a green run says otherwise.

    Newest only: an older fixture predates every upstream removal, so sunset
    rules still match it and report a miss that means nothing.

    Full bodies only: a `-scope` partial carries one section, so patches
    anchored outside it would miss for a reason that is not drift. The test is
    the marker the proxy itself patches on, not the filename -- a suffix says
    nothing about whether a body is whole.
    """
    versioned = [
        (prompt_patches.fixture_version(path), path)
        for path in sorted(prompt_patches.KB_DIR.glob("v*.md"))
        if prompt_location.BODY_MARKER in path.read_text()
    ]
    assert versioned, ("no full fixtures in", prompt_patches.KB_DIR)
    newest = max(version for version, _ in versioned)
    return [path for version, path in versioned if version == newest]


def captures() -> list[Path]:
    """Raw capture bodies, top level only -- `subagents/` bodies are never
    patched. Gitignored, so a machine that has never run the proxy has none,
    and a check that reads them can only skip."""
    return sorted(prompt_capture.PROMPTS_DIR.glob("*.raw.md"))


def capture_bodies() -> dict[str, str]:
    """Every capture body, `subagents/` included -- they are masked by the same
    rules, and are where overlapping-span bugs have shown up first. Only the
    keying laws want these; anything that patches a body wants `captures()`."""
    return {str(p): p.read_text() for p in sorted(prompt_capture.PROMPTS_DIR.rglob("*.raw.md"))}
