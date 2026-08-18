---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-000-mitmproxy-process-memory-ps-status-smaps-rollup-cmdline-fd-count.md
---

# Proxy RSS is ~526 MiB, at its all-time peak, and almost entirely Python heap

VmRSS 538,276 kB with VmHWM identical -- the process has never shrunk.
RssAnon is 524,628 kB, all private dirty (smaps_rollup Private_Dirty
matches exactly); RssFile is only ~13 MiB. So this is live allocator
heap, not mapped files or shared memory, and whatever holds it has held
it monotonically for the process's 28-hour life.
