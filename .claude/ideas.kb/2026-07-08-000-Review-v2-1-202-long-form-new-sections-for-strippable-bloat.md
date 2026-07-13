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

**Update 2026-07-12:** v2.1.202 was never promoted to `system-prompts.kb/`
before v2.1.207 superseded it (now promoted instead; see todo.md). This
review's target shifts to v2.1.207 -- diff against the same v2.1.199
baseline still captures 202's additive drift as a subset, so no
coverage is lost by skipping a 202-specific pass.

## Open Questions / Unknowns

- Which new spans contradict user instructions vs. merely restate them?
- Does the harness variant (v2.1.207-harness.md, also grown relative to
  v2.1.199-harness.md) carry parallel new content deserving the same
  review?

## Next Steps (if pursuing)

- [x] Diff `system-prompts.kb/v2.1.207.md` against `v2.1.199.md`,
  section by section
- [x] For each new/reworked span: strip (new patch dir), keep, or note
  contradiction
- [x] Same pass for `v2.1.207-harness.md` vs `v2.1.199-harness.md`

## Findings 2026-07-12

The original premise was wrong: `# Executing actions with care` and
`# Text output ...` are **not** new headers -- both already exist
verbatim at v2.1.199. The 15.0k -> 17.9k growth was almost entirely the
dynamic `# Environment` block (scratchpad path length, `git status`
dump size) varying by capture instance, not template growth -- see
`CLAUDE.kb/raw-capture-byte-diffs-include-dynamic-content.md` (new,
this session) for the general gotcha.

Long-form (v2.1.199.md -> v2.1.207.md), real (non-dynamic) content:
- `# Executing actions with care`'s body paragraph reworked/expanded:
  adds preferring a reversible step over deleting, running `git status`
  before destructive git commands, and checking for secrets before
  staging/pushing. **Assessment: keep, no patch.** Reinforces (doesn't
  contradict) conventions already in this user's own
  `~/.claude/reference.kb/git/*.md`; it's safety-additive, not the kind
  of company-serving bloat existing patches target.
- `# Session-specific guidance` bullets differ (`!`/fork tips vs.
  Agent/Explore tips) -- but this section is itself session-dependent
  (confirmed: this very session's live prompt carries the *new*
  `# Executing actions with care` body alongside the *old* `!`/fork
  bullets), so the swap is session variance, not version drift. Not
  actionable.

Harness (v2.1.199-harness.md -> v2.1.207-harness.md), real content:
- `# Harness`'s `<system-reminder>` bullet reworded (harness-injection
  framing -> "mid-conversation system turns" framing). Minor, doesn't
  contradict user instructions. **Assessment: keep, no patch.**
- A 4-paragraph "operating autonomously" block and the Fable-5
  model-family paragraph appear in v2.1.199-harness but not
  v2.1.207-harness. Likely mode/model-conditional (subagent
  autonomous-mode framing, model-family text already known to vary --
  `strip-model-family` exists for exactly this) rather than an upstream
  removal, but unconfirmed with only one capture per version -- would
  need multiple same-cc_version harness captures across session modes
  to disambiguate. Not pursued further this pass.

No new patches added. Closing -- reopen only if a future capture shows
these spans are stable and worth revisiting.

## Lifecycle

**Status:** Resolved -- no action
