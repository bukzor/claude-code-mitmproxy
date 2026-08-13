"""Replace built-in tool descriptions with slim stubs.

The patch half of `addons/toolpatch.py`, minus every mitmproxy concept: the
`tools` list in, mutated in place, incidents filed on the way. That is what
lets `check_tool_patches.py` exercise the same code the proxy runs.

Patch format and triage workflow: ~/.claude/tool-description-patches.d/README.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, NamedTuple

from claude_mitmproxy import incidents

PATCHES_DIR = Path("~/.claude/tool-description-patches.d").expanduser()


class ToolPatch(NamedTuple):
    name: str  # exact tool name == patch directory name
    upstreams: tuple[str, ...]  # last-reviewed upstream descriptions; drift tripwire
    replacement: str

    @staticmethod
    def load(directory: Path) -> ToolPatch:
        single = directory / "upstream.md"
        multi = directory / "upstream.d"
        assert not (single.is_file() and multi.is_dir()), (
            directory,
            "both upstream.md and upstream.d/ present",
        )
        assert single.is_file() or multi.is_dir(), (
            directory,
            "missing upstream.md or upstream.d/",
        )
        # rstrip: descriptions travel without a trailing newline; the files
        # carry one (text editors, jq -j both happen -- normalize either way).
        if single.is_file():
            upstreams = (single.read_text().rstrip("\n"),)
        else:
            files = sorted(p for p in multi.iterdir() if p.suffix == ".md")
            assert files, (multi, "no *.md files in upstream.d/")
            upstreams = tuple(p.read_text().rstrip("\n") for p in files)
        description_file = directory / "description.md"
        assert description_file.is_file(), (directory, "missing description.md")
        return ToolPatch(
            name=directory.name,
            upstreams=upstreams,
            replacement=description_file.read_text().rstrip("\n"),
        )


def load_tool_patches(patches_dir: Path) -> dict[str, ToolPatch]:
    """Every subdirectory of patches_dir is a patch: ToolPatch.load asserts on
    a malformed one (missing description.md) rather than this function
    silently dropping it -- a config error, not out-of-scope.

    An absent directory or an empty result is likewise a config error: the
    path is `~`-relative, so a wrong $HOME resolves it somewhere that
    doesn't exist, and returning {} there would read as "nothing to patch"
    instead of failing.
    """
    assert patches_dir.is_dir(), (patches_dir, "patches dir missing (wrong $HOME?)")
    patches = {
        child.name: ToolPatch.load(child)
        for child in sorted(patches_dir.iterdir())
        if child.is_dir()
    }
    assert patches, (patches_dir, "no patches found")
    return patches


def apply_tool_patches(
    tools: list,
    patches: Mapping[str, ToolPatch],
    capture_dir: Path | None = incidents.CAPTURE_DIR,
) -> None:
    """Mutate `tools` in place: replace each patched tool's description with
    its slim stub. A live description that no longer matches upstream.md still
    gets the stub -- the stub is self-contained -- but the live text is
    captured loudly for triage, since the stub may now be hiding new upstream
    guidance. Tools without a patch, and entries without a description
    (server tools), pass through untouched; absence is not drift."""
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        patch = patches.get(tool.get("name", ""))
        if patch is None or not isinstance(tool.get("description"), str):
            continue
        live = tool["description"].rstrip("\n")
        if live not in patch.upstreams:
            issue = incidents.Incident(f"tooldesc-{patch.name}", "changed-upstream")
            incidents.report_issues(live, [issue], capture_dir)
        tool["description"] = patch.replacement

