---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.5
    rationale: |
      Diff v2.1.202.md against v2.1.199.md, read the new/reworked
      sections against user CLAUDE.md, decide which spans earn patches.
  benefit-2w:
    "@value": 0.5
    rationale: |
      The new content is ~1.8k chars of unstripped prompt billed on
      every sonnet-class request, plus possible contradictions with
      user instructions (the usual reason patches exist).
---

# Review v2.1.202 long-form new sections for strippable bloat

## The Idea

The v2.1.202 long-form prompt grew 15.0k -> 17.9k chars with new
sections (`# Executing actions with care`, `# Text output (does not
apply to tool calls)`) and reworked wording. All existing patches still
apply cleanly (nothing went dark -- verified via `check_dark_patches.py`
2026-07-08), but none of them touch the new content: patched output
grew 10.2k -> 11.0k. Nobody has yet read the new sections asking the
project's motivating questions: does this contradict user CLAUDE.md?
is it bloat?

## Open Questions / Unknowns

- Which new spans contradict user instructions vs. merely restate them?
- Does the harness variant (v2.1.203-harness.md, also grown: 9.4k ->
  11.5k) carry parallel new content deserving the same review?

## Next Steps (if pursuing)

- [ ] Diff `system-prompts.kb/v2.1.202.md` against `v2.1.199.md`,
  section by section
- [ ] For each new/reworked span: strip (new patch dir), keep, or note
  contradiction
- [ ] Same pass for `v2.1.203-harness.md` vs `v2.1.199-harness.md`

## Lifecycle

**Status:** Exploring
