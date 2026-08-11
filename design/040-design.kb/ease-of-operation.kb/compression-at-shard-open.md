---
why:
  - ease-of-operation
---

# Shards are compressed when one is opened, from the response hook

Sharding bounds any single file but not the directory: `log/traffic/`
reached 7.6G before anyone looked, which is the same unattended-growth
failure `sharded-logs.md` addresses, one level up. Compression rather
than a retention window is what makes that a non-problem -- these
captures collapse ~55x, because every turn resends the system prompt and
the whole conversation prefix -- so nothing has to be thrown away and the
directory grows at roughly 20 MB/day instead of a gigabyte.

**The trigger is opening a shard, not rotating one.** Rotation looks like
the moment to act -- it is the only point at which the code *knows* a
shard just ended -- but this proxy is started by hand and stopped with
it: every shard's last write so far is an afternoon or evening one, so
no run has ever reached a midnight and a compressor hung off the
rotation branch would essentially never fire. Opening covers both
lifetimes with one rule, because at any open every shard but the new one
is finished: the ordinary restart-tomorrow pattern spawns at startup,
and a run long enough to cross midnight spawns at the roll.

Fire once per shard opened rather than once per open, so the reopen in
`rotation-self-heals.md` doesn't spawn a second child against the same
shard.

**The trigger belongs on the response hook, not the request hook.** Two
writers shard this directory independently. `flow2jsonl.py` owns the
`.jsonl` and rotates from `_emit`, which the request hook reaches first.
mitmproxy's own `Save` addon owns the `.flow` and rotates from
`save_flow`, which only the *response* hook reaches. So at the first
request of a new shard, the previous `.jsonl` is closed but the previous
`.flow` is still open. A compressor fired there would skip the `.flow`
-- correctly, since compressing under a live writer would lose
everything written after the archive was made -- and not revisit it
until the next shard opened, leaving the largest file uncompressed for a
day and a half.

Deferring the spawn to the end of the response hook fixes this by
ordering alone, with no sleeps and no polling: `Save` is a core addon, so
it precedes every `-s` script for the same hook, and by the time
`flow2jsonl.response` returns, both of the previous shard's files are
closed whichever hook noticed the date change first.

The trigger can afford to be generous because the child decides what is
finished: `compress_traffic.py` skips anything a process still holds
open and anything last written today, and takes a lock so a hand-run and
a spawned one cannot both write the same archive. Two smaller invariants
hold up the spawn itself. The child must inherit no file descriptors
(Python's `close_fds` default), or it would hold the very captures it is
deciding about. And a spawn is skipped while the previous child is
alive, so a proxy restarted repeatedly cannot stack compressors on the
same files.
