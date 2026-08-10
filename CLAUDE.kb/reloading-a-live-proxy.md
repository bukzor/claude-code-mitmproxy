# Reloading a live proxy: `touch reload.py`

mitmproxy polls every `-s` script's mtime once a second and re-executes
the ones that changed, so there is no "the running process is insulated
from edits on disk" assumption available while `proxy.sh` is up. The
polling loop is an asyncio task and every hook in this repo is a plain
synchronous function, so a reload lands between requests, never inside
one.

Only the `-s` scripts are watched. A module they import is rebound from
`sys.modules` without being re-executed, so editing `incidents.py`,
`templates.py` or `shapes.py` used to change nothing until a restart.
`syspatch.py` is watched *and* imported: mitmproxy loads `-s` scripts
under the name `__mitmproxy_script__.syspatch`, while `syscapture` does
`import syspatch` and gets an ordinary second copy. Re-executing the
addon copy leaves the library copy stale.

`reload.py` is the fix and the only place that does this: an `-s` script
with no hooks that `importlib.reload`s `templates`, `shapes`, `incidents`
and `syspatch`, in dependency order. `touch reload.py` and the next poll
picks up every code edit in the repo. There is nothing in the file to
edit -- mtime is the whole trigger, so a nonce would be pure git churn.

## Why every local import is `import x`, never `from x import y`

`importlib.reload` re-executes a module into its existing `__dict__`, so
holders of the *module object* see the new functions. A from-import
copies the reference at import time, and that copy is never updated --
the importing module keeps calling the old function forever, while
everything else moves on. The failure is silent: nothing breaks, the
edit just doesn't take.

So the convention is absolute across the repo, and `reload.py` asserts it
at load time (`check_no_local_from_imports`) rather than trusting it.
Adding one `from incidents import ...` anywhere fails the reload loudly
instead of half-applying it.

`from __future__`, stdlib and third-party from-imports are unaffected --
nothing reloads those.

## Manual on purpose

An mtime watch over the whole repo (`watchexec`, `entr`) would reload
half-written files, the same way editing a live `*-patches.d/` directory
makes every intermediate file state load-bearing and produces a burst of
`_uncaught-syspatch` assertions. Restart-on-change was the other option
and was rejected outright: it drops in-flight connections, which for a
proxy in front of Claude Code means visibly killing someone's turn.

## The 2026-07-25 precedent

Observed while reworking `flow2jsonl.py`'s output-path handling on an
already-running proxy: mid-edit, the live process's TUI started spamming
raw text. Best-evidence explanation: the reload re-ran `load(loader)`,
which re-declares the `jsonl_path` option, and something in that path
reset the option's live value to its declared default (`/dev/stdout`)
instead of preserving the `--set jsonl_path=...` from the original
invocation -- so the addon's JSON streamed into the curses UI's stdout.
Root cause never traced into mitmproxy's option-reload internals.

That hazard is specific to an addon that declares options in `load()`,
which is `flow2jsonl.py` alone. `reload.py` declares none and registers
no hooks. But it is the reason to reload deliberately and then look, not
to reload continuously and hope.
