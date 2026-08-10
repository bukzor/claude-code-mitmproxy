"""On-demand reload of this repo's shared modules: `touch reload.py`.

mitmproxy re-executes an `-s` script when its mtime advances, but only that
script. A module the script imported is rebound from `sys.modules` without
being re-executed, so editing `incidents.py` or `templates.py` under a live
proxy changes nothing -- and `syspatch.py` exists twice, since `syscapture`
imports it as a library: mitmproxy re-executes the addon copy and leaves the
library copy stale. This addon is the one designated place that re-executes
all of them, and the only reason a code edit here needs no restart.

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

import incidents
import shapes
import syspatch
import templates

# Dependency order: reloading a module re-executes its own imports, so it has
# to see already-reloaded versions of what it builds on.
RELOADED = (templates, shapes, incidents, syspatch)

LOCAL_FROM_IMPORT = re.compile(
    rf"^from ({'|'.join(m.__name__ for m in RELOADED)}) import", re.MULTILINE
)


def check_no_local_from_imports() -> None:
    """Refuse to reload while any module here does `from x import y` on a local
    module. A from-import copies the reference, so the importer keeps the old
    function object forever, and reloading quietly updates everyone except it.
    `import x` with `x.y()` at the call site resolves through the module object
    `importlib.reload` mutates in place, so one reload reaches every holder --
    but only while the convention holds everywhere, which is why it is checked
    rather than documented."""
    offenders = [
        f"{path.name}:{line}"
        for path in sorted(Path(__file__).parent.glob("*.py"))
        for line in LOCAL_FROM_IMPORT.findall(path.read_text())
    ]
    assert not offenders, (offenders, "local from-import defeats reload.py")


check_no_local_from_imports()
for module in RELOADED:
    importlib.reload(module)
logging.info("reloaded %s", ", ".join(m.__name__ for m in RELOADED))
