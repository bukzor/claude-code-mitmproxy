---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-009-baseline-rss-of-new-headless-mitmdump-process-pid-19340.md
  - ../evidence.kb/2026-08-21-000-rss-of-headless-mitmdump-pid-29920-after-2d19h.md
---

# Under headless mitmdump, RSS growth is ~30x slower than the pre-fix leak

~99 MiB baseline (pid 19340, 2026-08-18) to 141 MiB after ~66.6 h of live
multi-session traffic (pid 29920, 2026-08-21) -- ~0.63 MiB/h, versus the
pre-fix ~18.8 MiB/h (526 MiB in 28 h, TUI view store). This is the
day-after fix verification `../todo.kb/2026-08-18-000-...md` step 4 called
for; the remaining slow creep reads as ordinary allocator/heap growth
under a long-lived process, not a reintroduced per-flow retention leak,
but wasn't watched long enough to rule out a slower unbounded leak on its
own -- see `../todo.kb/` for whether that's worth a longer watch or a
monitoring bound instead.
