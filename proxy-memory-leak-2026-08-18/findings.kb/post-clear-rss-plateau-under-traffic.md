---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-006-rss-flat-line-watch-after-clear-15-x-60s.md
  - ../evidence.kb/2026-08-18-007-traffic-during-plateau-watch-shard-growth-since-14-46.md
---

# After the clear, RSS sat dead flat under heavy traffic

Fifteen one-minute samples, 15:11-15:25: 558,600 -> 558,604 kB, +4 kB
total. Meanwhile the day's flow shard grew ~57 MB (176 MB at 14:46 to
233 MB at 15:27) -- the same traffic level that had driven ~93 MB/h of
RSS growth before the clear. New flows are being allocated inside the
~400 MB the clear freed: the store was the holder. This is the
pre-registered confirm criterion from
`../root-cause.kb/console-flow-store-retention.md`.
