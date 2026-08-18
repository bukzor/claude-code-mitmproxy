---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-001-system-memory-state-free-pressure-meminfo.md
  - ../evidence.kb/2026-08-18-002-kernel-oom-traces-in-dmesg.md
---

# No OOM has occurred, but the host has no swap and ~3.4 GiB headroom

dmesg has no oom/kill lines. MemAvailable is ~3.4 GiB of 14.5 GiB, and
memory-pressure stall averages are currently zero (nonzero lifetime
totals show past stall). With zero swap configured, the eventual failure
mode of unbounded growth is an abrupt OOM kill -- of the proxy or of one
of the similarly-sized claude processes -- rather than gradual thrash.
