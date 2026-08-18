---
last-updated: 2026-08-18
---

# Root cause: confirmed -- the mitmproxy TUI's unbounded flow store

`proxy.sh` ran the proxy as the interactive `mitmproxy` TUI, whose View
addon retains every flow in an in-memory OrderedDict with no eviction
(mitmproxy 12.2.3, `addons/view.py`; by design for an interactive tool).
Claude Code traffic is enormous per flow -- the full conversation plus a
multi-hundred-KB system prompt re-sent on every call -- so the store
grew at traffic rate: ~526 MiB RSS after 28 h, ~93 MB/h during busy
stretches, monotonic (VmRSS == VmHWM whenever sampled). The mismatch
was running an interactive tool as an unattended long-running service;
neither this repo's addons (audited clean,
`./findings.kb/repo-addons-retain-no-per-flow-state.md`) nor mitmproxy
itself is at fault.

Confirmed 2026-08-18 15:25 by the pre-registered test: `:view.clear`
emptied the store, and RSS then sat flat (+4 kB over 15 min) under
traffic that grew the disk shard ~57 MB
(`./findings.kb/post-clear-rss-plateau-under-traffic.md`). Only ~20 MiB
returned to the OS -- glibc keeps the freed heap for reuse
(`./findings.kb/view-clear-returned-little-to-os.md`) -- which is why
the plateau, not an RSS drop, is the signature.

Fix: `proxy.sh` now execs headless `mitmdump` (no view store; event log
on stderr), effective at the next restart --
`./remediations.kb/run-headless-mitmdump.md`; verification staged in
`./todo.kb/2026-08-18-000-confirm-store-retention-and-adopt-a-bound.md`.

Why the alternatives lost: `./root-cause.kb/repo-addon-accumulation.md`
(static audit found no retained per-flow state),
`./root-cause.kb/allocator-fragmentation.md` (cannot produce
traffic-proportional growth; its real contribution is the ~540 MB of
allocator-held RSS the cleared process still shows, which the plateau
proves is being reused, not leaked).
