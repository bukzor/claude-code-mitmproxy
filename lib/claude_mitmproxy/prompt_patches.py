"""Apply modular patches to the Claude Code system prompt, and judge the
result in aggregate.

The patch half of `addons/syspatch.py`, minus every mitmproxy concept: text
in, text out, incidents filed on the way. That is what lets the six offline
checks exercise the same code the proxy runs -- `capture_dir=None` and they
measure without filing anything.

Where the prompt body *is* in a request is `prompt_location`; this module is
only what to do with one once you have it.
"""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path

from claude_mitmproxy import incidents
from claude_mitmproxy import repo_paths
from claude_mitmproxy import prompt_shape
from claude_mitmproxy import rule_templates


def apply_patches(
    text: str,
    patches: tuple[rule_templates.Rule, ...],
    capture_dir: Path | None = incidents.CAPTURE_DIR,
    origin: incidents.Origin = incidents.Origin(),
) -> str:
    """`rule_templates.apply_rules` plus this project's loudness policy: a patch
    that proved itself in scope and then failed to find its target is an
    incident, captured content-addressed so it warns exactly once. Which
    misses are worth a warning is the caller's call, not the engine's --
    masks run the same templates and are never loud."""
    patched, misses = rule_templates.apply_rules(text, patches)
    if misses:
        issues = [incidents.Incident(*miss) for miss in misses]
        incidents.report_issues(text, issues, capture_dir, origin)
    return patched


# --- aggregate strip-rate tripwire ---

KB_DIR = repo_paths.ROOT / "system-prompts.kb"
BLOCKS_DIR = repo_paths.ROOT / "blocks.d"
STRIP_RULE = "_strip-rate"


def fixture_version(path: Path) -> tuple[int, ...]:
    release = path.stem.removeprefix("v").split("-")[0]
    return tuple(int(part) for part in release.split("."))


@functools.lru_cache(maxsize=1)
def strip_floors(patches: tuple[rule_templates.Rule, ...]) -> dict[str, int]:
    """Minimum bytes the patch set must strip from a live body, per prompt
    shape: half of what it strips from the *core* of the newest promoted
    fixture of that shape -- the fixture with every session-optional block
    (`blocks.d/`) deleted, which is the sparsest body that shape can take.
    Newest by version, then size, so a full capture beats a `-scope`
    partial.

    Calibrating on the core is what keeps the floor underneath a minimal
    live session. A fixture carries whatever blocks its capturing session
    happened to switch on, and those can be most of what the patch set
    strips: v2.1.227-fable strips 2295 bytes, 1485 of them block-dependent,
    so the floor it used to imply (1147) sat above the 980 a git-less,
    scratchpad-less fable session strips -- a tripwire that fires on
    ordinary traffic, which is the noise `earned-silence` forbids. Halving
    was meant to absorb that gap and cannot when the gap is over half. With
    the blocks already gone, halving is headroom for genuine drift instead,
    and an upstream rewrite still sends every shape-scoped patch dark, far
    below any floor. `check_strip_floors.py` is the offline detector.

    Cached per patch set -- Rule stores templates as strings, so
    value-equal loads share one entry; a fixture promoted mid-process is
    picked up by `touch lib/claude_mitmproxy/addons/reload.py`, which
    rebuilds this module and the cache with it."""
    newest: dict[str, tuple[tuple, str]] = {}
    for path in KB_DIR.glob("v*.md"):
        text = path.read_text()
        shape = prompt_shape.shape_of(text)
        if shape.startswith("?"):
            continue
        key = (fixture_version(path), len(text))
        if shape not in newest or key > newest[shape][0]:
            newest[shape] = (key, text)
    assert newest, (KB_DIR, "no classifiable fixtures")
    blocks = rule_templates.load_templates(BLOCKS_DIR)
    floors: dict[str, int] = {}
    for shape, (_, text) in newest.items():
        # Masks first: block templates are written against the tokens masks
        # leave behind (`blocks.d/README.md`).
        core, _present = rule_templates.strip_blocks(incidents.normalize_body(text), blocks)
        # `apply_rules`, not `apply_patches`: a core body is synthetic, so a
        # patch missing it is an artifact of the masking and the cuts, not
        # evidence about upstream, and warning here would put that artifact
        # in the log on every reload.
        floors[shape] = (len(core) - len(rule_templates.apply_rules(core, patches)[0])) // 2
    return floors


def check_strip_floor(
    original: str,
    patched: str,
    patches: tuple[rule_templates.Rule, ...],
    capture_dir: Path | None,
    origin: incidents.Origin = incidents.Origin(),
) -> None:
    """The aggregate check no per-patch rule can provide: an upstream
    rewrite sends every shape-scoped patch silently out of scope at once,
    and per-patch loudness reports that as nothing (2026-08-04 incident,
    see session.kb). A patched main body must strip at least its shape's
    floor; a body matching no known shape is the same alarm one step
    earlier."""
    shape = prompt_shape.shape_of(original)
    floor = strip_floors(patches).get(shape)
    stripped = len(original) - len(patched)
    if floor is None:
        issue = incidents.Incident(STRIP_RULE, f"unknown-shape-{shape}")
    elif stripped < floor:
        issue = incidents.Incident(
            STRIP_RULE, f"low-strip-{shape}-{stripped}B-floor-{floor}B"
        )
    else:
        return
    incidents.report_issues(original, [issue], capture_dir, origin)


# Re-read per request by the addon, so editing a patch takes effect without a
# restart (`CLAUDE.kb/patches-reread-per-request.md`). Under `~`, not in-repo:
# patches encode one operator's preferences (`design/010-mission.kb/`).
PATCHES_DIR = Path("~/.claude/system-prompt-patches.d").expanduser()
