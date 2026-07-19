---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.5
    rationale: |
      Diff v2.1.214.md against v2.1.207.md (and v2.1.212-harness.md
      against v2.1.207-harness.md), read the new sections against user
      CLAUDE.md, decide which spans earn patches. Same shape and same
      timebox as the 2026-07-08-000 review this supersedes.
  benefit-2w:
    "@value": 0.5
    rationale: |
      Two new real (non-dynamic) sections riding on every sonnet-class
      and fable-class request since v2.1.208-ish; possible contradictions
      with user instructions are the usual reason patches exist here.
---

# Review v2.1.207-to-214 new long-form sections for strippable bloat

## The Idea

The 2026-07-18 promotion pass (`v2.1.207` -> `v2.1.214` long-form,
`v2.1.207-harness` -> `v2.1.212-harness`) surfaced two new real template
sections neither prior review pass covered:

- A they/them pronoun-default paragraph appended to `# Text output` (the
  "when you use a pronoun for someone" guidance).
- A whole new `# Background Session` section (present in both the
  long-form and harness captures), describing background-job behavior:
  don't call yourself "a background agent", use `$CLAUDE_JOB_DIR/tmp`
  instead of `/tmp`, skip `EnterWorktree` when configured to work in
  place.

Nobody has yet read these against the project's motivating questions:
does either contradict user CLAUDE.md? Is either bloat worth stripping?

## Potential Benefits

- The pronoun paragraph may already be redundant with (or contradict)
  user conventions -- worth a quick check.
- The `# Background Session` section is entirely new subject matter
  (background-job framing); unclear yet whether it's ever
  patch-relevant or just inert for interactive sessions.

## Open Questions / Unknowns

- Does the pronoun-default paragraph restate something the user's own
  CLAUDE.md already covers, making it strippable bloat?
- Is `# Background Session` present in every capture or only
  session-mode-dependent (like the `# Session-specific guidance`
  bullets were found to be in the prior review)? Only one capture
  instance exists per version so far -- can't yet distinguish "new
  upstream content" from "this particular session ran as a background
  job."

## Exploration Notes

Prior review (`2026-07-08-000`, resolved 2026-07-12) found that most
apparent growth between captures was dynamic content (scratchpad path,
`git status` dump length), not real template drift -- see
`CLAUDE.kb/raw-capture-byte-diffs-include-dynamic-content.md`. Apply the
same skepticism here: confirm each span is real template text before
treating it as new, the same way that review corrected its own initial
"new headers" premise.

## Next Steps (if pursuing)

- [ ] Diff `system-prompts.kb/v2.1.214.md` against `v2.1.207.md`,
  isolate the real (non-dynamic) spans
- [ ] For each new/reworded span: strip (new patch dir), keep, or note
  contradiction
- [ ] Same pass for `v2.1.212-harness.md` vs `v2.1.207-harness.md`
- [ ] Determine whether `# Background Session` is session-mode-gated by
  capturing an ordinary (non-background) session at the same cc_version

## Lifecycle

**Status:** Exploring
