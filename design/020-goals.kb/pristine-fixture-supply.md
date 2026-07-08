---
why:
  - offline-validation
---

# Pristine fixture supply

Offline validation is only as good as its fixtures, and the proxy's own
logs cannot supply them: they record requests post-rewrite, so a body
extracted there is contaminated precisely when patches work. Fixtures
are therefore captured by a dedicated addon ahead of all mutation —
automatically and deduplicated — so every prompt variant the proxy ever
sees is available pristine, including versions that appeared once,
before anyone knew to look for them.
