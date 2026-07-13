"""Replace built-in tool descriptions with slim stubs via mitmproxy.

Patch format and triage workflow: ~/.claude/tool-description-patches.d/README.md.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Mapping, NamedTuple

from incidents import CAPTURE_DIR, Incident, capture_uncaught, report_issues

PATCHES_DIR = Path("~/.claude/tool-description-patches.d").expanduser()

UNCAUGHT_RULE = "_uncaught-toolpatch"


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
    silently dropping it -- a config error, not out-of-scope."""
    if not patches_dir.is_dir():
        return {}
    return {child.name: ToolPatch.load(child) for child in sorted(patches_dir.iterdir()) if child.is_dir()}


def apply_tool_patches(
    tools: list,
    patches: Mapping[str, ToolPatch],
    capture_dir: Path | None = CAPTURE_DIR,
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
            issue = Incident(f"tooldesc-{patch.name}", "changed-upstream")
            report_issues(live, [issue], capture_dir)
        tool["description"] = patch.replacement


# --- mitmproxy addon ---


def load(loader):
    """Called once at mitmproxy startup. Patches are re-read from disk on
    every request (see _request) so editing `*-patches.d/` takes effect
    immediately -- this hook only logs what's configured at startup."""
    del loader  # unused
    patches = load_tool_patches(PATCHES_DIR)
    logging.info("loaded %d tool description patches", len(patches))
    for patch in patches.values():
        logging.info(
            "  %s (%d upstream variants -> %d chars)",
            patch.name,
            len(patch.upstreams),
            len(patch.replacement),
        )


def request(flow):
    """mitmproxy request hook. Wraps _request so a bug here lands in the same
    content-addressed capture as a patch-application issue, instead of only
    flashing through mitmproxy's own log."""
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
    tools = request.get("tools")
    if not isinstance(tools, list):
        return

    apply_tool_patches(tools, load_tool_patches(PATCHES_DIR))
    flow.request.set_content(json.dumps(request).encode())
