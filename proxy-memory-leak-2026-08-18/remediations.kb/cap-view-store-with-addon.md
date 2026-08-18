---
status: rejected
requires-sudo: false
---

# Add a store-cap addon (durable fix, keeps the TUI)

Rejected 2026-08-18: the user doesn't use the flow list, only the event
log, so `run-headless-mitmdump.md` gets the same bound with negative
rather than positive complexity.

A small `-s` addon whose `response` hook evicts oldest flows once the
view store exceeds a cap (e.g. 200 flows / ~50 MB): call
`ctx.master.commands.call("view.flows.resolve", "@all")` slice +
`view.flows.remove`, or track ids in a deque. Bounds memory forever
while keeping recent flows browsable; disk shards remain the archive.
Touches this repo's invariants (addon order, addons/ membership,
loudness) -- read `design/` before implementing, per project CLAUDE.md.
