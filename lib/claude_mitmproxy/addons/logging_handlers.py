"""mitmproxy addon: give this repo's event records somewhere to land.

Loaded first, before every other `-s` script, so the startup inventories the
other addons log from their own `load` hooks are already being captured when
they run.

A module-level config addon with no hooks, like `reload.py` and `quietconn.py`:
there is no flow to act on, and re-execution is the reload. The work is in
`logging_handlers`, which imports without mitmproxy; this file exists only to
be the thing mitmproxy re-executes.
"""

from claude_mitmproxy import logging_handlers

logging_handlers.reinstall_log_handlers()
