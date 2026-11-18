"""`addons/reload.py` executes cleanly: its own invariants hold.

It asserts on import -- every addon-imported library module is named in
`RELOADED`, nothing reaches into a reloaded module by name -- and nothing else
runs it, so a library change that breaks one of them is invisible until a live
proxy re-executes the file or fails to start. Run in a subprocess: a reload
rebinds module state, which is not something to do inside the test process.

With logging disabled: the reload ends by emitting `lifecycle.reload` into the
real `log/events/`, a domain the live proxy writes and holds locked, so an
enabled run either forges a reload record or files an `_uncaught-events-log`
incident against the operator's queue. Disabled, the emit call still executes
-- a broken line still fails here -- and no record reaches a handler.
"""

from __future__ import annotations

import subprocess
import sys

from claude_mitmproxy import repo_paths

RELOAD = repo_paths.ROOT / "lib" / "claude_mitmproxy" / "addons" / "reload.py"


def test_reload_addon_executes():
    result = subprocess.run(
        [sys.executable, "-c", f"import logging, runpy; logging.disable(); runpy.run_path({str(RELOAD)!r})"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
