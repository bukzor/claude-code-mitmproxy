---
why:
  - final-say-over-injected-behavior
---

# Offline validation

Every live rewrite has an offline checker (`check_patches.py`,
`check_tool_patches.py`, `check_dark_patches.py`) that applies the same
code paths to captured fixtures. A patch edit is validated in seconds
against every known prompt shape — no proxy, no session, no token
spent. "Zero warnings against the newest capture" is the release
criterion for any patch change.
