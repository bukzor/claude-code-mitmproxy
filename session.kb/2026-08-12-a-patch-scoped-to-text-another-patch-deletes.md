# 2026-08-12: a patch scoped to text another patch deletes

## How it surfaced

Not by looking for it. The day's work was structural: give every `check_*.py`
one shape — `collect()` gathers, `render()` formats, `PREDICATES` judges — so
the hand-run command and `monitoring/` could assert the *same function objects*
instead of two copies of one idea.

`check_dark_patches.py` was the last one converted, and it had no predicate.
Its own docstring had named the property worth asserting for months
(SUBSUMPTION: raw match hits, patched match doesn't), and
`monitoring/CLAUDE.md` recorded that it was "not asserted yet". Writing it as
a predicate took four lines, because the data was already being computed for
the table. It came back red on the first run.

## What was wrong

`strip-help-feedback` matched on the heading `# Doing tasks`, and
`strip-doing-tasks-bloat` — earlier in load order, which is alphabetical —
deletes that heading. By the time the later rule's turn came, its scope test
found nothing, so it reported itself inapplicable and did nothing.

`--pattern` settled what that cost: the text the rule exists to remove
**SURVIVES** into every long-form session, on every fixture where the rule is
subsumed. It has been dead for as long as both rules have existed.

## Why nothing was loud

By design, and correctly. A `match` miss is how a rule reports its own
irrelevance — wrong prompt variant, session-optional content absent — so it is
silent, and no flag changes that. Nothing at proxy time can distinguish "not
applicable here" from "someone else got here first"; both are a rule declining
to fire.

The `_strip-rate` floor could not catch it either. Floors are calibrated from
the fixtures through the same patch set, so a rule that strips nothing lowers
the floor by exactly what it fails to strip. A patch dying takes its own
tripwire down with it.

That leaves the offline sweep, which needs the whole pipeline replayed in order
against every fixture to see it at all — which is what the matrix already did,
and had been printing, uninterpreted, the whole time.

## What changed

`match.md` now holds the rule's own target text and `search.md` is gone — the
match-only idiom `strip-additional-dirs` and `strip-security-bloat` already
use. A rule that matches on what it deletes cannot be scoped out by whatever
ran before it; the order-dependence was the defect, not the ordering.

The patch set strips 232 more chars, and `prompt_patches.strip_floors` recalibrated
the long-form floor 2435 → 2551 with every capture still clearing it.

Sunset rows are exempt from the predicate: an upstream-removed rule asserts
text is gone, so on a fixture predating the removal, our own earlier patch
deleting it first is the expected reading.

## What stays open

The generalization. This was a rule whose `match` named text *outside* its own
deletion — the only way a patch can be scoped out by a sibling. Nothing forbids
writing another one, and nothing but this predicate would notice. Whether
`match` should be *required* to overlap the rule's own target is a real
question and is not settled here.
