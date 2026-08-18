---
status: likely
evidence:
  - ../evidence.kb/2026-08-18-003-traffic-volume-since-proxy-start-flow-and-jsonl-shard-sizes.md
  - ../evidence.kb/2026-08-18-000-mitmproxy-process-memory-ps-status-smaps-rollup-cmdline-fd-count.md
---

# The heap size is the same order as the raw traffic the process has seen

Today's shard was already 176 MB of raw flows (plus 180 MB JSONL) by
14:46, and 2026-08-17's compressed shard (8.4 MB zst) implies a similar
raw day. Lifetime raw traffic through this process is therefore roughly
300-400 MB; the anonymous heap is 512 MiB. Python object overhead on
retained flows comfortably covers the gap -- consistent with "the
process keeps every flow", inconsistent with a small metadata leak.
