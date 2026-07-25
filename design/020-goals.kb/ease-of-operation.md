---
why:
  - final-say-over-injected-behavior
---

# Ease of operation

A proxy nobody wants to babysit stops being run, and an unrun proxy gives
the user no say at all. So the proxy must survive being left alone:
unattended for weeks between restarts, and restarted without notice or
ceremony when it is.

Success looks like: no output grows without bound just because the
process didn't restart, and no restart -- planned or accidental --
silently discards data the previous run had already captured.
