---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-000-mitmproxy-process-memory-ps-status-smaps-rollup-cmdline-fd-count.md
---

# No file-descriptor or thread leak

28 open fds and 17 threads after 28 hours -- both normal for mitmproxy
with six addons. The growth is memory only.
