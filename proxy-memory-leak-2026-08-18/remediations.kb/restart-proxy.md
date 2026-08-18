---
status: proposed
requires-sudo: false
---

# Restart the proxy (blunt recovery)

Ctrl-C the TUI in tmux and rerun `proxy.sh`. Restarts append to the
day's shards by design (design/040-design.kb/ease-of-operation.kb/), so
the only loss is in-TUI history plus a few seconds of proxying (live
Claude Code sessions retry). Inferior to clear-view-store-now.md in
every way except not requiring the TUI to be responsive.
