---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-004-vmrss-after-user-ran-view-clear.md
  - ../evidence.kb/2026-08-18-005-rss-after-user-ran-view-clear.md
---

# view.clear emptied the store but returned only ~20 MiB to the OS

RSS had grown 538 -> 579 MB between 14:43 and 15:09 (~93 MB/h under
that half-hour's heavy traffic). After the user's `view.clear`, RSS fell
to 558,600 kB -- the first time in the process's 28-hour life that
VmRSS sat below VmHWM -- but ~420 MB stayed resident. Expected glibc
behavior: the freed flow objects return to the allocator (reusable
heap), not the OS, so the confirming signal is RSS *plateauing* under
traffic rather than dropping. A 15-minute watch is filed as the
subsequent rss-flat-line evidence capture; the definitive test is the
headless-mitmdump switch, which removes the store entirely.
