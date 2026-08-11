---
why:
  - pristine-fixture-supply
  - offline-validation
---

# Fixture lifecycle

1. `syscapture.py` writes each unique pre-patch prompt body to
   `log/prompt-captures/` (gitignored) as
   `v{cc_version}_{model}_{digest}.raw.md` plus a masked `.md` sibling —
   automatic, deduplicated by masked digest but *named* by the raw one, so
   a `masks.d/` edit never renames a capture
   (`content-addressed-capture.md`).
2. A human promotes noteworthy captures' `.raw.md` into
   `system-prompts.kb/` under that collection's naming rules (version,
   `-variant`, `-scope`).
3. `check_patches.py` defaults to the newest *unsuffixed* full capture:
   sunset patches assert against the current prompt, so warnings
   against older fixtures are expected, not regressions.
4. On promotion, run `check_patches.py` (expect zero warnings) and
   `check_dark_patches.py` (expect no unexplained newly-dark patches).

Step 2 has no automatic trigger — additive upstream drift is invisible
to every loud mechanism until someone looks — so `survey_captures.py` is
that look: one row per capture, with shape, session-optional blocks, and
whether this exact body is already promoted.

Beside each capture's raw digest the survey prints a *core* digest: the
masked body hashed again after the session-optional blocks (`blocks.d/`)
are stripped too. Rows sharing a core are the same prompt modulo which
blocks that session happened to carry, so only an unseen core is worth
hand-diffing.
Stripping blocks never reaches `masked_hash` — see
`content-addressed-capture.md` for why block presence has to stay in the
capture identity — but it is not confined to this view: `strip_floors`
calibrates the `_strip-rate` tripwire on a fixture's core for the same
reason the survey digests one, so that what a session happened to switch
on doesn't count as prompt copy. The per-row block flags are
the names of the rules that fired, so a rule that stops matching drops its
flag and moves the core digest together. Flags and core digest cannot
disagree about which rule was there, because no two block rules delete
overlapping bytes
(`keying.claims.kb/this-proxy.kb/block-spans-are-disjoint.md`).
