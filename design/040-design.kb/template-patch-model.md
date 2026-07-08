---
why:
  - earned-silence
  - offline-validation
---

# Template patch model

Patches are declarative directories of literal-text templates with
`$PLACEHOLDER` holes — not diffs, not hand-written regexes. Literal
text survives upstream reformatting better than line-anchored diffs,
stays readable as prose, and compiles to a regex only as an
implementation detail.

The `match`/`search` split is what makes earned silence expressible:
`match` (is this patch applicable to this body at all?) anchors on
stable structure like section headings; `search` (the precise text to
replace) carries the exact wording. Drift *within* an asserted scope is
loud, while out-of-scope absence stays silent.

Normative format specs: `~/.claude/system-prompt-patches.d/README.md`
and `~/.claude/tool-description-patches.d/README.md`.
