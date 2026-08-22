# binpatch and its SessionStart hook

`binpatch.py` substitutes bytes in the installed Claude Code binary to undo
behavior that is compiled into the CLI, has no setting/env/hook to change, and
never crosses the wire -- the one class of Claude Code behavior a proxy patch
cannot reach. Every substitution is equal-length (offsets and executable
structure stay valid); the bun binary embeds the bundle twice, so a patch
expects two hits and refuses to write on any other count (`Drift`).

## Why a hook, and why it "errors out"

There is no Claude Code hook event for "an update was installed" (the binary's
own event-name table has none). An auto-update drops a fresh, unpatched binary
and repoints `~/.local/bin/claude`; updates are far more frequent than
`proxy.sh` restarts, so the proxy is the wrong place to re-apply.

SessionStart is the re-apply point. It runs before the model's first turn, and
its stderr on exit 2 renders to the *user* as a hook-error notice while the
session proceeds (the model never sees it) -- exactly "warn me, don't block."
The just-started session already mapped the old code from memory, so a
just-applied patch cannot help it: the message says restart. `os.replace` swaps
a new inode in without writing the busy one, so patching the running binary is
safe (no ETXTBSY) and the live process keeps its old inode until it exits.

Steady state: after an update, the first session's hook re-patches the new
binary and tells you to restart; every session after that finds it already
patched and exits 0 in silence (one mmap scan, no 342 MB read, no write).

## The wiring (lives in a different repo)

`~/.claude/settings.json` -> `hooks.SessionStart`, matcher `startup|resume`
(the fresh-process cases), shell form so `$HOME` expands:

    "SessionStart": [
      { "matcher": "startup|resume",
        "hooks": [ { "type": "command",
          "command": "\"$HOME\"/claude/mitmproxy/lib/claude_mitmproxy/binpatch.py" } ] } ]

The hook execs the module file directly by its shebang -- it is stdlib-only
with no local imports, so it needs neither the venv nor `uv run` on the
session-start hot path.

## On drift (exit 1)

A patch's byte pattern no longer appears `expect` times pristine nor patched:
Claude Code changed the code the patch targeted. Nothing is written. Re-derive
against the new binary -- locate the target
(`strings -a <binary> | grep -n <anchor>`, then `dd`/`od` around the byte
offset from `grep -abo`), confirm the two embedded copies, and update
`PATCHES`. `tengu_subagent_md_report_blocked` was the telemetry key for the
guard the first patch removes; the message was "Subagents should return
findings as text, not write report files."
