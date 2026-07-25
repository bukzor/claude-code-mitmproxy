---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.25  # SWE-hours (one SWEh ≈ 60 focused minutes)
    rationale: |
      Small: incidents.py already exposes normalize_body(); this is
      deciding whether save_body's contract should change and doing the
      mechanical write-both-files edit.
  benefit-2w:
    "@value": 0.5  # or just: 2.0
    rationale: |
      log/patch-failures/ incidents are triaged individually (one body per
      failure), not diffed against each other the way prompt-captures
      versions are — the motivating pain point (noisy diffs across
      captures) doesn't obviously apply. Marginal benefit unless triage
      workflow starts wanting normalized-vs-raw comparison too.
---

# Normalized sibling for patch-failures bodies

## The Idea

2026-07-11: `log/prompt-captures/` now writes both the verbatim body
(`.raw.md`) and a hash-normalized sibling (`.md`, via the new
`incidents.normalize_body()`) — the normalized one is the low-noise
day-to-day diff target, raw is for auditing/promotion. `incidents.py`'s
other capture site, `save_body()` (backing `log/patch-failures/_bodies/`),
still writes only the verbatim body. Per `design/040-design.kb/
content-addressed-capture.md`, both sites share one primitive and were
previously symmetric (verbatim-only); this idea is whether to extend the
same pair-write to `save_body`/`log/patch-failures/` for consistency.

## Potential Benefits

- Symmetry: one mental model for "what content-addressed capture
  writes" instead of two.
- If triage ever wants to eyeball a failure body with session noise
  stripped (e.g. comparing two incidents under different rules that hit
  the same underlying drift), the normalized sibling is already there.

## Open Questions / Unknowns

- Is there an actual triage workflow that wants this, or is symmetry
  the only argument? `log/patch-failures/` incidents are usually read one
  at a time (`CLAUDE.kb/patch-failure-triage.md`), not diffed against
  each other — the noisy-diff problem that motivated the prompt-captures
  change may not exist here.
- `_body_still_live`/`archive_incident` (incidents.py) move/prune the
  body file by digest; a second sibling file would need the same
  archive/prune treatment or it'd orphan.

## Exploration Notes

If pursued: `save_body` would write `{digest}.raw.md` +
`{digest}.md`, and `archive_incident`'s body-move logic would need to
move both. Check callers that read `_bodies/{digest}.md` directly
(triage tooling, `gc_patch_failures.py`) for assumptions about a single
file.

## Next Steps (if pursuing)

- [ ] Check whether `CLAUDE.kb/patch-failure-triage.md` or triage habit
      ever wants a masked view of a failure body.
- [ ] If yes: extend `save_body`/`archive_incident` to the pair, update
      `content-addressed-capture.md`.

## Lifecycle

**Status:** Exploring
