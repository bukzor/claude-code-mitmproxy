---
managed-by: Skill(llm-subtask)
status: Exploring
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 0.3  # SWEh value created over 2w if this pans out
---

# Audit heading-anchored match.md templates for self-referential collision risk

## The Idea

`condense-delivering-work/match.md` was a bare literal `# Delivering work`
with no line-start anchor, so it matched inside this repo's own captured
`gitStatus` (commit `873f6da`'s message mentions the heading by name, not
as a heading) instead of the real prompt section — see
`CLAUDE.kb/patch-failure-triage.md`'s "Not present at all — match fired on
this project's own text" for the 2026-08-20 incident and fix (leading `\n`
anchor). Every other patch whose `match.md`/`match.d/*.md` is a bare
`# Heading` with no leading newline has the same latent exposure: it only
needs a future commit message, session note, or `session.kb`/`todo.kb` entry
to quote that heading by name.

## Potential Benefits

Fixing pre-emptively avoids a repeat `failed-to-match` false alarm (cheap
but not free — triage time, a body capture, a diff) the next time this
project's own history mentions a patch's target heading.

## Open Questions / Unknowns

- How many of the ~20 patch dirs use a bare-heading anchor with no leading
  `\n`? (`condense-corrections/match.md` = `# Corrections` is the most
  obvious sibling — already checked clean against current git log, but
  that's a snapshot, not a guarantee.)
- Is a leading `\n` ever wrong to add? (No case found yet — real headings
  are always preceded by a blank line in every fixture checked.)
- Worth a `check_laws.py`-style static assertion instead of a one-time
  manual pass, so new patches can't reintroduce the gap?

## Exploration Notes

Triage doc's own guidance is not to blanket-fix this pre-emptively — "fix it
where it's actually fired" — so this stayed an idea rather than a todo.

## Next Steps (if pursuing)

- [ ] Grep all `match.md`/`match.d/*.md` under
      `~/.claude/system-prompt-patches.d/` for a bare `# ` opener with no
      leading `\n`; for each, prepend the anchor if a promoted fixture
      confirms the real heading is always preceded by a blank line.
- [ ] Consider a `check_laws.py` (or new checker) assertion instead, so the
      class of bug can't recur unnoticed.

## Lifecycle

**Status:** Exploring
