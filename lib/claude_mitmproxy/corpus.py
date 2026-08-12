"""The bodies every check reads, resolved through the module that writes them.

Nothing here resolves a path against the cwd. These same loaders serve the
hand-run commands and the `monitoring/` suite, so a check run from another
repo's session reads exactly what a run from this checkout reads -- and the
two halves of a check cannot disagree about which bodies they examined.
"""

from __future__ import annotations

import re
from pathlib import Path

from claude_mitmproxy import syscapture
from claude_mitmproxy import syspatch

# Full-body fixture name; -scope partials (e.g. v2.1.128-doing-tasks.md) excluded.
FIXTURE_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)\.md$")


def fixtures() -> dict[Path, str]:
    """The promoted fixtures, newline-terminated: a template ending "\\n" needs
    end-of-body to read as a line boundary, the same normalization
    `apply_masks` does before matching. Committed, so these are always here."""
    paths = sorted(p for p in syspatch.KB_DIR.glob("*.md") if p.name != "CLAUDE.md")
    assert paths, syspatch.KB_DIR
    texts = {p: p.read_text() for p in paths}
    return {p: t if t.endswith("\n") else t + "\n" for p, t in texts.items()}


def latest_fixture() -> Path:
    """Highest-versioned full fixture. Validating against the current prompt
    keeps upstream-removed assertions silent; older fixtures still trip them
    (their text predates the removal), so anything asking "do the patches still
    land" means this one."""
    versioned = [
        (tuple(int(g) for g in m.groups()), p)
        for p in syspatch.KB_DIR.iterdir()
        if (m := FIXTURE_RE.match(p.name))
    ]
    assert versioned, ("no vMAJOR.MINOR.PATCH.md fixtures in", syspatch.KB_DIR)
    return max(versioned)[1]


def captures() -> list[Path]:
    """Raw capture bodies, top level only -- `subagents/` bodies are never
    patched. Gitignored, so a machine that has never run the proxy has none,
    and a check that reads them can only skip."""
    return sorted(syscapture.PROMPTS_DIR.glob("*.raw.md"))


def capture_bodies() -> dict[str, str]:
    """Every capture body, `subagents/` included -- they are masked by the same
    rules, and are where overlapping-span bugs have shown up first. Only the
    keying laws want these; anything that patches a body wants `captures()`."""
    return {str(p): p.read_text() for p in sorted(syscapture.PROMPTS_DIR.rglob("*.raw.md"))}
