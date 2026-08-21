---
why:
  - ../010-mission.kb/final-say-over-injected-behavior.md
---

# Earned silence

A rewriting proxy's natural failure mode is silence: the target drifts,
the rewrite stops applying, and nobody notices for months. This
happened — `strip-over-engineering` was dark from v2.1.76 until an
audit found it.

So silence must be earned. A component may stay quiet about a
non-action only when it holds evidence the non-action is correct: a
fixture the patch was verified against, or a recognized non-interactive
request shape. Any other anomaly is loud — and exactly once per
distinct content, so loudness stays actionable instead of becoming
noise someone learns to mute.
