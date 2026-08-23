---
why:
  - ../010-mission.kb/final-say-over-injected-behavior.md
---

# Decoupled from the CLI

All rewriting happens on the wire, between the stock CLI and the API.
The proxy needs no knowledge of the CLI's internals — only of the
request shapes it emits, which the capture layer keeps under continuous
observation.

**Why not patch `cli.js`:** couples to a binary that updates weekly and
re-breaks on every release. **Why not pin an old CLI version:** trades
the problem for a stale CLI.

**The binpatch exception.** A little injected behavior is compiled into
the binary and never sent — e.g. the `Write` guard that rejects
sub-agent `*.md` reports. The wire is no lever for it, so the reasons
above don't bite: there is no on-wire alternative to trade against the
coupling. `binpatch.py` patches the binary for that class alone,
accepting the coupling this goal otherwise rejects — it does re-break on
every release. The cost is bounded, not avoided: a `SessionStart` hook
re-applies it idempotently, and equal-length, drift-loud substitutions
keep a silently-moved target from patching the wrong bytes. The goal
stands for everything reachable on the wire, which is everything else.
