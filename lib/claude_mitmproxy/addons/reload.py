"""On-demand reload of this repo's shared modules: `touch reload.py`.

mitmproxy re-executes an `-s` script when its mtime advances, but only that
script. So every module in `addons/` reloads itself for free, and nothing in
the library beside it does: an edited `incidents.py` or `rule_templates.py` is
rebound from `sys.modules` without being re-executed, and a live proxy goes on
running the old code. This addon is the one designated place that re-executes
all of them, and the only reason a library edit needs no restart.

The trigger is deliberately manual, and there is nothing in this file to edit:
mitmproxy polls mtime once a second, so `touch` alone does it. An automatic
watch would reload half-written files, the way editing a live patch directory
makes every intermediate state load-bearing. Because that poll is an asyncio
task and every hook in this repo is synchronous, a reload lands between
requests and never inside one.
"""
from __future__ import annotations

import importlib
import logging
import re
from pathlib import Path

from claude_mitmproxy import flocked_logs
from claude_mitmproxy import gc_patch_failures
from claude_mitmproxy import incidents
from claude_mitmproxy import logging_handlers
from claude_mitmproxy import prompt_capture
from claude_mitmproxy import prompt_location
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import prompt_shape
from claude_mitmproxy import repo_paths
from claude_mitmproxy import rule_templates
from claude_mitmproxy import tool_patches

# Dependency order: reloading a module re-executes its own imports, so it has
# to see already-reloaded versions of what it builds on.
RELOADED = (
    repo_paths,
    flocked_logs,
    # Re-executing this reinstalls the events handler, which is the whole
    # reason it may be reloaded at all: it holds no module state, so the
    # replacement finds the live handler by name and its fd by scanning.
    logging_handlers,
    rule_templates,
    prompt_shape,
    incidents,
    gc_patch_failures,
    prompt_location,
    prompt_patches,
    prompt_capture,
    tool_patches,
)

PACKAGE = Path(__file__).parent.parent
ADDONS = Path(__file__).parent

LOCAL_FROM_IMPORT = re.compile(
    rf"^from ({'|'.join(m.__name__ for m in RELOADED)}) import", re.MULTILINE
)
ADDON_IMPORT = re.compile(
    r"^(?:from|import) claude_mitmproxy\.addons\b|^from claude_mitmproxy import addons\b",
    re.MULTILINE,
)
LIBRARY_IMPORT = re.compile(r"^from claude_mitmproxy import (\w+)", re.MULTILINE)


def check_no_local_from_imports() -> None:
    """Refuse to reload while any module here reaches *into* a reloaded module:
    `from claude_mitmproxy.rule_templates import compile`. That copies the
    reference, so the importer keeps the old function object forever, and
    reloading quietly updates everyone except it. Naming the module instead --
    `from claude_mitmproxy import rule_templates`, `rule_templates.compile()` at the call
    site -- resolves through the module object `importlib.reload` mutates in
    place, so one reload reaches every holder. Both spellings start `from`,
    which is why this matches the dotted path rather than the keyword, and why
    it is checked rather than documented."""
    offenders = [
        f"{path.name}:{line}"
        for path in sorted(PACKAGE.rglob("*.py"))
        for line in LOCAL_FROM_IMPORT.findall(path.read_text())
    ]
    assert not offenders, (offenders, "local from-import defeats reload.py")


def check_addons_unimported() -> None:
    """Refuse to reload while anything outside `addons/` imports an addon.
    `addons/` earns its name by holding exactly what mitmproxy `-s`-loads
    (`addons/__init__.py`); a check importing `addons.toolpatch` for the patch
    logic would put addons and libraries back in one bag. Whatever it wants is
    in the library module the addon delegates to -- which, unlike the addon,
    imports without mitmproxy installed."""
    offenders = [
        str(path.relative_to(PACKAGE.parent))
        for path in sorted(PACKAGE.rglob("*.py"))
        if path.parent != ADDONS and ADDON_IMPORT.search(path.read_text())
    ]
    assert not offenders, (offenders, "addons are loaded, not imported")


def check_reloaded_covers_addon_imports() -> None:
    """Refuse to reload while an addon imports a library module RELOADED
    doesn't name. mitmproxy re-executes the addon, so the addon's own edits
    land; what it holds is rebound from `sys.modules` and keeps running the
    code the proxy started with. That is the whole failure this file exists to
    prevent, and it is invisible from the outside -- the stale module goes on
    working, correctly, from an old definition. Checked rather than
    documented, because the way it goes wrong is someone adding an import
    three files away and never coming here."""
    named = {module.__name__.rsplit(".", 1)[-1] for module in RELOADED}
    imported = {
        name
        for path in sorted(ADDONS.glob("*.py"))
        for name in LIBRARY_IMPORT.findall(path.read_text())
    }
    assert not imported - named, (
        sorted(imported - named),
        "addon-imported module missing from RELOADED",
    )


check_no_local_from_imports()
check_addons_unimported()
check_reloaded_covers_addon_imports()
for module in RELOADED:
    importlib.reload(module)
# Reloading logging_handlers rebinds its class but not the live instance, which
# would go on running pre-edit code from the old class -- the exact staleness
# this file exists to prevent, one rung out. Reinstalling here is what makes
# module-reload and addon-reload synonymous; importing must stay side-effect
# free, so the call belongs at the two reload sites rather than in that module.
logging_handlers.reinstall_log_handlers()
# An event, not a log line: which code a live proxy is actually running is a
# fact that was previously announced once, to a terminal nobody reads, and then
# lost -- so a reload that half-succeeded looked exactly like one that never
# happened. Emitted after the reinstall above, which is what gives it a file.
logging.getLogger(logging_handlers.LIFECYCLE_RELOAD).info(
    "reloaded %s", ", ".join(m.__name__ for m in RELOADED)
)
