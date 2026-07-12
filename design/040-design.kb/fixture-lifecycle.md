---
why:
  - pristine-fixture-supply
  - offline-validation
---

# Fixture lifecycle

1. `syscapture.py` writes each unique pre-patch prompt body to
   `prompt-captures/` (gitignored) as
   `v{cc_version}_{model}_{digest}.raw.md` plus a masked `.md` sibling —
   automatic, deduplicated by masked digest.
2. A human promotes noteworthy captures' `.raw.md` into
   `system-prompts.kb/` under that collection's naming rules (version,
   `-variant`, `-scope`).
3. `check_patches.py` defaults to the newest *unsuffixed* full capture:
   sunset patches assert against the current prompt, so warnings
   against older fixtures are expected, not regressions.
4. On promotion, run `check_patches.py` (expect zero warnings) and
   `check_dark_patches.py` (expect no unexplained newly-dark patches).
