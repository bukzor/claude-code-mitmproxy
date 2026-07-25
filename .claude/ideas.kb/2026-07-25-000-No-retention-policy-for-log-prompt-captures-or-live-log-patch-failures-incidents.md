---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.5
    rationale: |
      Deciding the retention rule (age? "already promoted"?
      "already archived and un-referenced"?) is the real cost; the
      mechanical gc-loop part is small (gc_patch_failures.py is a
      template to copy).
  benefit-2w:
    "@value": 0.25
    rationale: |
      Neither directory is close to a problem today (prompt-captures/
      1.4M, patch-failures/ live incidents even smaller) -- this is
      pre-emptive, not a fix for observed pain.
---

# No retention policy for log/prompt-captures or live log/patch-failures incidents

## The Idea

2026-07-25's `log/` reorg (unifying proxy output under one gitignored
parent, day-sharding the unbounded traffic capture) surfaced that the
two content-addressed capture dirs still have asymmetric retention:

- `log/patch-failures/_archive/` is age-pruned by `gc_patch_failures.py`
  (30-day default), but *live* (non-archived) incidents under
  `log/patch-failures/{rule}/` have no gc at all -- they sit until
  someone manually triages and archives them
  (`CLAUDE.kb/patch-failure-triage.md`).
- `log/prompt-captures/` has no gc of any kind. It grows by one entry
  per distinct system-prompt body ever seen, deduped by content hash,
  forever -- including bodies long since promoted into
  `system-prompts.kb/` and no longer needed in their pre-promotion form.

## Potential Benefits

- Bounded disk use without a human remembering to look, matching the
  "ease of operation" goal (`design/020-goals.kb/ease-of-operation.md`)
  already established for the traffic capture.
- One less thing on the standing-maintenance checklist to eyeball.

## Open Questions / Unknowns

- For `prompt-captures/`: is "already promoted to system-prompts.kb/"
  a safe deletion trigger, or does the pre-promotion pair (`.raw.md` +
  masked `.md`) carry information the promoted copy doesn't (e.g. the
  masked sibling, which system-prompts.kb/ doesn't keep)?
- For live `patch-failures/` incidents: these are unresolved-by-design
  (a human hasn't triaged them yet) -- age-pruning a live incident
  would silently drop an unfixed problem, which is a different failure
  mode than pruning an already-resolved archive entry. May not want gc
  here at all, just a loudness/visibility mechanism instead.

## Next Steps (if pursuing)

- [ ] Decide the `prompt-captures/` retention trigger (promoted? aged?
      neither) before writing any gc code -- the wrong trigger silently
      destroys fixture history.
- [ ] Decide whether live `patch-failures/` incidents should ever be
      pruned automatically, or whether the actual gap is visibility
      (e.g. surfacing incident age) rather than deletion.

## Lifecycle

**Status:** Exploring
