---
status: done
requires-sudo: false
---

# Clear the TUI flow store (immediate recovery, doubles as root-cause test)

Done 2026-08-18 ~15:09 by the user. Store emptied; only ~20 MiB came
back to the OS (`../findings.kb/view-clear-returned-little-to-os.md`) --
the quiet outcome the test anticipated, so confirmation shifted to the
plateau watch and the headless switch (`run-headless-mitmdump.md`).

In the running mitmproxy TUI (tmux): `:view.clear` (or the `z` binding
on the flow list). Every flow is already persisted to the day's .flow
and .jsonl shards, so nothing is lost except the scrollable in-TUI
history. Watch `grep VmRSS /proc/$(pgrep -f 'bin/mitmproxy')/status`
before/after; this is the confirm/kill test in
../root-cause.kb/console-flow-store-retention.md. Repeatable whenever
RSS annoys, at zero downtime.
