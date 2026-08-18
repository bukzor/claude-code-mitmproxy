---
status: confirmed
evidence:
  - ../evidence.kb/2026-08-18-003-rss-growth-sample-12-x-20s.md
---

# RSS creeps steadily upward, never dipping, even under light traffic

Twelve samples over 3.7 minutes: 538,392 kB -> 538,592 kB, +200 kB with
no decreases (~3 MB/h at that moment's load). The lifetime average is
much higher: assuming a startup baseline around 130-150 MiB (typical
mitmproxy TUI + these addons; not measured -- the process predates the
investigation), roughly 380 MiB accumulated over 28 h ≈ 14 MB/h,
concentrated in busy periods.
