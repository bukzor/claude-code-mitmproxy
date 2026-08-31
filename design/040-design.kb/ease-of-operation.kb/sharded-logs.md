---
why:
  - ../../020-goals.kb/ease-of-operation.md
---

# Sharded logs

Any output whose size has no natural bound -- currently the live
`traffic.{flow,jsonl}` capture -- is written to a strftime-templated path
(`log/traffic/%Y-%m-%d.flow`), never a fixed filename: each day gets its
own shard, so a restart-free run doesn't grow one file forever and
`find -size +1G` never becomes the normal state of the repo.

Content-addressed outputs (`log/patch-failures/`, `log/prompt-captures/`)
don't need this: each item is small and named by its own hash, so the
directory can only grow by distinct content, never by wall-clock time.

`log/events/` is sharded despite being tiny -- a few lines a day, ~13 KB a
month measured. Size is not the only thing a date in the path buys: it is what
makes a shard **finished**, and a finished file is the unit compression,
retention and `held_open()` all act on. An events file with no date is never
done being written and so can never be handed to any of them. The naming is
`<category…>/<type>.<date>.log`, date as a leaf suffix so one glob spans a
type's whole history and `.log` stays the suffix `compress_traffic` reads; a
stable `tail -F` target is a symlink beside it, which GNU tail follows across
the swap, reopening from the start so no line is lost at midnight.

The size argument still governs *compression*, which is a separate question
from sharding: `compressible()` takes a minimum size so a 440-byte shard is
not archived into a 300-byte `.zst`.
