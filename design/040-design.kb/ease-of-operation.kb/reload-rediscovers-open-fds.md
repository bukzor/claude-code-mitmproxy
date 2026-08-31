---
why:
  - ../../020-goals.kb/ease-of-operation.md
---

# An open file survives reload by being rediscovered, not remembered

**Addon-reload and module-reload are exactly synonymous.** Neither gets a
teardown hook, neither may be special-cased, and any code holding an OS
resource has to be re-runnable in a process that already holds it.

That rules out remembering the fd. mitmproxy re-executes an edited `-s` script
into a *fresh* namespace (`load_script` pops it from `sys.modules` first), so
the previous execution's globals are unreachable; `importlib.reload` re-executes
a library module into its *existing* `__dict__`, so a module-level
`_FD = None` would clobber the only reference and leak the fd with its lock.
The two paths fail in opposite directions, which is why one rule has to cover
both: keep no module state, and recover from the runtime instead.

Two syscall facts make that recovery exact, and they are a matched pair:

- Re-`flock`ing the fd that already holds the lock succeeds as a no-op.
- A *second* fd on the same file conflicts even within one process, because
  the lock belongs to the open file description rather than to the process.

So scanning `/proc/self/fd` for our own fds on the path and trying `flock` on
each in turn both finds the holder and, when none succeeds, *proves* the file
is held by somebody else -- the scan is exhaustive over our own fds, so the
remaining holder cannot be us. A leaked reload and a second proxy are told
apart with no `/proc/locks` lookup and no pid bookkeeping; the second is an
error worth raising, and the first is invisible.

`flocked_logs.reopen_flocked_file` is that primitive.
`reopen_log_file` layers day-sharding on it: recompute the shard from the date,
close any of our fds on the log's *other* shards, open the current one. Only
that log's shards -- a sibling log in the same directory keeps its fd and its
lock.

This is the stronger form of [rotation-self-heals]. That entry defends a
cached `_current_path`/`_fp` pair against falling out of sync, after the pair
went silently dark for hours on 2026-07-25. Here there is no pair: the path is
derived per call and the fd is found by scanning, so the desync it repairs is
not representable. New writers should take this shape; `flow2jsonl` keeps the
older one until something else makes it worth moving.

Testing this needs one warning. Assertions about a *closed* fd number prove
nothing, because `os.open` immediately recycles it -- a test written that way
passes against code that closes the wrong file. Assert on lock state observed
from another process, and on `self_fd_targets()`, never on fd identity. Both
tests written the wrong way here survived the mutation that should have killed
them.

[rotation-self-heals]: rotation-self-heals.md
