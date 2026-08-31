# 2026-08-31 -- events get their own channel

The proxy logged everything through `logging`, mitmdump sent the lot to stderr,
`proxy.sh` captured none of it. Facts the proxy knew exactly once -- "this
prompt body had never been seen before" -- were announced to a terminal and
lost. This session built the channel that keeps them.

## What the measurements changed

The task's own justification was wrong, and measuring it first is what caught
that. `driftwatch.sh` was said to wake ~290 times a day across three
directories, with an events file cutting that to ~5. But `log/prompt-captures/`
is content-addressed -- `save_prompt` writes only on a new masked digest -- so
it *already* changes only on news. Measured: the predicate costs 1.03s, real
captures run ~4/day over a 30-day sample, and 288 of the ~290 wakes are the
300s ceiling. The events file removes ~0.7% of them.

What the swap does buy is narrower and worth keeping: a `masks.d/` edit makes
`load_masked_digests` rewrite every stale masked sibling on the next request, a
burst of up to ~150 `close_write` events, each costing a re-derivation for an
input the predicate does not read. And only one of the three watches can ever
be replaced -- promoting a fixture is a hand edit, not a proxy event, and
promoting is what clears a standing report. The ~10x is in the ceiling, not in
the channel.

## Two design rulings, both the operator's

**Addon-reload and module-reload are exactly synonymous.** The first design
proposed hiding the handler class where `importlib.reload` could not reach it,
so a live instance could never go stale against a rebound class. The ruling
inverted it: no `done()`, no `DoneHook`, no special-casing either path, and an
idempotent reinstall that *replaces* the stale instance rather than avoiding
it. That is why the module holds no state at all -- the handler is found in the
`logging` registry, the fd by scanning `/proc/self/fd` -- and why the library
module keeps the code.

**Date-sharding, against a proposal to skip it.** The argument for skipping was
that events are ~13 KB/month and the date is already in every line, making a
dated path a redundant index. The rebuttal that settled it: these files are
time-series output like `log/traffic/`, not content-addressed artifacts like
`log/prompt-captures/`, and a date in the path is what makes a shard
*finished* -- the unit compression, retention and `held_open()` all act on. The
redundant-index argument proved too much; it would strip the date from
`log/traffic/` too, where every record also carries a timestamp.

Also ruled: `/proc/self/fd` alone suffices, no `/proc/locks`. Because the scan
is exhaustive over our own fds, a failure on the fresh open *proves* the holder
is foreign, so the pid was only ever decoration on the error string.

## Two tests that passed while proving nothing

Both found by mutation, both the same shape, and worth remembering because
neither looked wrong.

`os.open` immediately recycles a just-closed fd number. A test asserting
`fstat`/`flock` on a closed fd therefore passes against code that closed the
*wrong* file -- which is exactly the mutation (drop the sibling-log guard, so
rotating one log closes every other log's fd) that survived. Fixed by asserting
on lock state observed from another process, and on `self_fd_targets()`.

pytest's `caplog` captures records by a route that survives `propagate = False`.
A `caplog` assertion for "events still reach the console" therefore passes
against a handler that has stopped reaching the root entirely. Confirmed
directly -- the same mutation empties `caplog.text` in an isolated test but not
in the full file -- rather than reverse-engineering the plugin. Fixed with a
spy handler on the root logger.

## What the live proxy taught

Unit-green is not live-green, and the gap was real: a nine-name taxonomy
shipped with two emitters wired. Nothing had appeared under `log/events/`, and
the reason was legitimate -- `capture.*` cannot fire until upstream serves a
novel body, and none had crossed since the change. But `lifecycle.reload` had
happened repeatedly that afternoon, every time mitmproxy re-executed an edited
addon, and it was still going to `logging.info` on an unread terminal. Wiring
it produced the first real event on the first try, and `/proc/<pid>/fd` showed
the running proxy holding the shard -- the held-fd design confirmed in
production rather than in tests.

That check also surfaced the edge now filed in the todo: the proxy holds the
shard flock for its lifetime, so a second emitting process gets
`BlockingIOError`. Correct by design, but it bounds what an offline tool may
do. The full suite and `monitoring/` are green with the proxy holding the lock.

## Still true when this was written

`proxy.sh` gained `-s logging_handlers.py` first in the load order, but the
running proxy predates that line: it installed the handler via `reload.py`'s
call instead. The intended ordering -- load first, so the other addons' `load`
hooks are captured -- only takes effect at the next proxy start.
