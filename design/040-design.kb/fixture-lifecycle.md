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
2. `survey_captures --promote` files every copy the newest release serves
   that no fixture covers: the `.raw.md`, copied verbatim into
   `system-prompts.kb/` under a name derived from the capture (that
   collection's naming rules -- release, `-variant`, `-<digest>`), and
   committed. No step of that is a decision, so none of it waits on a
   human (ruled 2026-09-01: "that's the usual case for correct handling of
   the event. if that turns out to be false we should revisit").
3. `check_patches.py` reads every full fixture at the newest release:
   upstream serves several bodies at once, and a patch that misses on any
   of them misses in production. Newest only, because sunset patches
   assert against the current prompt, so warnings against older fixtures
   are expected, not regressions.
4. The promoting commit runs `check_patches.py` (expect zero warnings) and
   `check_dark_patches.py` (expect no unexplained newly-dark patches) by
   itself: a commit into `system-prompts.kb/` is one of the occasions that
   runs the whole offline suite (`every-duty-has-an-occasion.md`). Running
   them by hand is for seeing the answer, not for remembering to. A refused
   commit leaves the fixture on disk, uncommitted, and names what to fix.

Step 2 has an occasion. Additive upstream drift -- text no fixture covers --
is invisible to every tripwire, but the capture that carries it is an event
(`events-are-separate-from-logs.md`), and `driftwatch.sh` wakes on it,
re-evaluates which copies at the newest release lack a fixture, and promotes
them (`every-duty-has-an-occasion.md`). `survey_captures.py` is the same
question asked by hand: one row per capture, with shape, session-optional
blocks, and whether this exact body is already promoted; `--drift` narrows
that to one row per uncovered (shape, core), and `--current` to the newest
release. Coverage is read off the fixtures rather than off captures that
equal one, so a fixture whose capture has since been cleaned up still counts
as covering its copy.

What a reader still owes each promotion is a glance, and the glance is for
one failure. A fixture that differs from an existing one only in text a
`masks.d/` or `blocks.d/` rule should have neutralized is not a new copy but
flawed deduplication, and every fixture filed after it is the same mistake
again. So each promotion is reported with its diff against the nearest
fixture already on disk -- nearest meaning the smallest diff, found by
diffing against every other fixture (ruled 2026-09-01: "What *I* would mean
is the fixture with the smallest diff. Can we get away with exhaustive
diffing?"). The reader is the maintenance session that armed the watch, and
the diff arrives on its channel keyed by event type.

Exhaustive is quadratic in the fixture set and cheap at its current size. It
is kept honest by a time budget rather than by an index: a pass that overruns
the budget says so, with what it measured (fixtures compared, seconds spent),
so the moment to build something smarter announces itself instead of being
guessed at now (`loudness-policy.md`, on what a tripwire is for).

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
