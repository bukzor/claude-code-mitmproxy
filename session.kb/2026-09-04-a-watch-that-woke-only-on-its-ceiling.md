# 2026-09-04 -- a watch that woke only on its ceiling

## What happened

`driftwatch.sh` was switched on 2026-09-01 (f83c39a) from watching
`log/prompt-captures/` to watching `log/events/capture/`, the shard the
proxy appends a line to when it captures a body it has not seen, and its
polling ceiling was raised from five minutes to an hour on the strength of
that. Two defects, found three days apart, meant no capture ever woke it.

The first was caught while building it. The events handler appends through
an fd it holds for the proxy's lifetime, so the `close_write` inotify event
the watch listened for would arrive only when the proxy exited; `modify` had
to join the event set. That one was verified live before the commit.

The second was not. `save_prompt`'s contract since 5fedd10 was to return the
raw path when freshly written and None when already captured, and
`syscapture` emits the capture event only on a path. The function wrote both
files and fell off the end: no commit had ever contained the return, so no
capture event had ever been written, and `log/events/capture/` was empty
across the ten live captures since the emitter landed. Fixed in 06c345b,
with a test that pins the return on both branches.

## Why nothing was loud

The ceiling did exactly what it exists to do. A watch whose trigger never
fires degrades to polling, and polling at an hour still produced a correct
report, at most an hour late; nothing in the output distinguishes "woke on a
capture" from "woke on the clock". The "verified live" on the events channel
(657b6f1) had covered the lifecycle event only, and the capture event's test
exercised the logger rather than the emitter's condition, which is where the
gap was. A test that hands a logger a message proves the channel; it says
nothing about whether anything ever calls it.

## What changed

The return, and a test on both branches (06c345b). The lesson for the next
emitter is the general one: test the condition that emits, not the logger it
emits to; and when a fallback is designed to mask a silent failure, check the
primary path directly rather than reading the fallback's silence as the
primary working.
