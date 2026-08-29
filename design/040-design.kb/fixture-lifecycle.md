---
why:
  - ../020-goals.kb/pristine-fixture-supply.md
  - ../020-goals.kb/offline-validation.md
---

# Fixture lifecycle

1. `addons/syscapture.py` writes each unique pre-patch prompt body to
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

Looking is not the same as finding, though, and at ~100 captures the
inventory stopped fitting the duty it serves: the question is which
*copies* lack a fixture, and the table answers it only by eye, one
grouping and set-difference at a time. `--drift` computes that instead —
one row per uncovered (shape, core), newest first, naming the raw to
promote. Coverage is read off the fixtures rather than off captures that
equal one, so a fixture whose capture has since been cleaned up still
counts as covering its copy. The judgment stays human: the tool ranks by
recency and reports how many captures carry each copy, because the newest
copy and the copy that keeps recurring are not always the same one, and
which to promote is a call about what upstream is actually serving.

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
