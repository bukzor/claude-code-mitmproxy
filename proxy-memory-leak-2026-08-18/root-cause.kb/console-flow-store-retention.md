---
status: confirmed
---

# Console View store retains every flow of very large traffic

Mechanism: the proxy runs as the interactive `mitmproxy` TUI, whose View
addon keeps every flow in an unbounded in-memory OrderedDict
(`../findings.kb/console-flow-store-is-unbounded.md`). Claude Code traffic is
enormous per flow -- each API call re-sends the whole conversation plus
a multi-hundred-KB system prompt -- so a day of use is hundreds of MB of
bodies, all retained.

Supports: monotonic all-anonymous growth at exactly traffic scale
(`../findings.kb/rss-at-all-time-peak-all-anonymous.md`,
`../findings.kb/rss-magnitude-matches-traffic-volume.md`,
`../findings.kb/steady-growth-under-light-traffic.md`); repo addons
exonerated (`../findings.kb/repo-addons-retain-no-per-flow-state.md`).

Confirm: in the live TUI run `:view.clear` (everything is already
persisted to the .flow and .jsonl shards, so nothing is lost) and watch
`VmRSS`. Store emptied + growth restarting from near-zero confirms even
if glibc returns pages to the OS lazily; a large immediate RSS drop is
the loud version.

Test result 2026-08-18 15:09: the quiet outcome
(`../findings.kb/view-clear-returned-little-to-os.md`) -- store emptied,
~20 MiB returned, remainder allocator-held. Confirmed 15:25 by the
plateau: +4 kB of RSS across 15 minutes of traffic heavy enough to have
driven ~93 MB/h before the clear
(`../findings.kb/post-clear-rss-plateau-under-traffic.md`).

Kill (not triggered): RSS continuing to climb at the prior rate after a
clear, or climbing while the proxy is provably idle.
