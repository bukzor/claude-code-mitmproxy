# Editing a `-s` addon file while the proxy is live triggers a hot-reload

mitmproxy watches every `-s` script's mtime and reloads it in-process
when it changes -- there is no "the running process is insulated from
edits on disk" assumption available while `proxy.sh` is up. This applies
to `syscapture.py`, `syspatch.py`, `toolpatch.py`, `thinkpatch.py`,
`flow2jsonl.py` specifically (the `-s` scripts). Modules they import
(`incidents.py`, `templates.py`, `shapes.py`) are not watched, and the
reload does not refresh them either: re-running an `import` statement
rebinds a name from `sys.modules` rather than re-executing the module,
so their module-level state -- `incidents.masks()`'s cache, notably --
survives every hot-reload. Editing those needs a real restart.

Observed 2026-07-25 while reworking `flow2jsonl.py`'s output-path
handling on an already-running proxy: mid-edit, the live process's TUI
started spamming raw text. Best-evidence explanation: the reload re-ran
`load(loader)`, which re-declares the `jsonl_path` option, and something
in that path reset the option's live value back to its declared default
(`/dev/stdout`) instead of preserving the `--set jsonl_path=...` value
from the original invocation -- so the addon's own request/response JSON
started streaming straight into the curses UI's stdout. Root cause not
fully traced into mitmproxy's option-reload internals; the fix applied
was pragmatic, not diagnostic.

Consequence: treat any multi-file edit to the addon set as needing a
clean restart afterward, not a live one. Don't rely on the mid-edit
state being coherent enough to observe or debug -- restart, then look.
