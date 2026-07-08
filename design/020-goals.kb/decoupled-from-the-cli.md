---
why:
  - final-say-over-injected-behavior
---

# Decoupled from the CLI

All rewriting happens on the wire, between the stock CLI and the API.
The proxy needs no knowledge of the CLI's internals — only of the
request shapes it emits, which the capture layer keeps under continuous
observation.

**Why not patch `cli.js`:** couples to a binary that updates weekly and
re-breaks on every release. **Why not pin an old CLI version:** trades
the problem for a stale CLI.
