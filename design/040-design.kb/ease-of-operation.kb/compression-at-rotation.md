---
why:
  - ease-of-operation
---

# Shards are compressed at the day roll, from the response hook

Sharding bounds any single file but not the directory: `log/traffic/`
reached 7.6G before anyone looked, which is the same unattended-growth
failure `sharded-logs.md` addresses, one level up. Compression rather
than a retention window is what makes that a non-problem -- these
captures collapse ~55x, because every turn resends the system prompt and
the whole conversation prefix -- so nothing has to be thrown away and the
directory grows at roughly 20 MB/day instead of a gigabyte.

The day roll is the moment to act, since it is the only time a shard is
known to be finished. **The trigger belongs on the response hook, not
the request hook**, and that is the whole subtlety:

Two writers shard this directory independently. `flow2jsonl.py` owns the
`.jsonl` and rotates from `_emit`, which the request hook reaches first.
mitmproxy's own `Save` addon owns the `.flow` and rotates from
`save_flow`, which only the *response* hook reaches. So at the first
request after midnight, yesterday's `.jsonl` is closed but yesterday's
`.flow` is still open. A compressor fired there would skip the `.flow`
-- correctly, since compressing under a live writer would lose
everything written after the archive was made -- and not revisit it
until the *next* day's roll, leaving the largest file uncompressed for a
day and a half.

Deferring the spawn to the end of the response hook fixes this by
ordering alone, with no sleeps and no polling: `Save` is a core addon, so
it precedes every `-s` script for the same hook, and by the time
`flow2jsonl.response` returns, both of yesterday's files are closed
whichever hook noticed the date change first.

Two smaller invariants hold it up. The child must inherit no file
descriptors (Python's `close_fds` default), or it would hold the very
captures it is deciding about. And a run is skipped while the previous
child is alive, so a proxy restarted repeatedly across a day roll cannot
stack compressors on the same files.
