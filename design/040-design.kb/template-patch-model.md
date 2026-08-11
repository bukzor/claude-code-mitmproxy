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

There are two hole types and no third: `$NAME` spans the rest of a line,
`$...LINES` spans a run of non-blank lines. Both stop at structure they
cannot consume — a line break, a blank line — so the literal on either
side of a hole is a delimiter that always exists. A hole that could cross
blank lines has no such bound and is not offered; `load_templates`
rejects the one that used to be
(`keying.claims.kb/this-proxy.kb/no-hole-may-cross-a-blank-line.md`).

The `match`/`search` split is what makes earned silence expressible:
`match` (is this patch applicable to this body at all?) anchors on
stable structure like section headings; `search` (the precise text to
replace) carries the exact wording. Drift *within* an asserted scope is
loud, while out-of-scope absence stays silent.

Template compilation lives in `templates.py`, imported by every
consumer: `syspatch.py` for the prompt patches, `incidents.py` for the
capture-digest masks (`content-addressed-capture.md`), and
`survey_captures.py` for the block strippers (`fixture-lifecycle.md`).
Applying a rule set *returns* its unapplied rules rather than reporting
them, so the caller owns the loudness decision — which is what lets one
format serve a mechanism whose misses are loud and ones whose misses are
silent by construction.

Normative format specs: `~/.claude/system-prompt-patches.d/README.md`
and `~/.claude/tool-description-patches.d/README.md`; the in-repo rule
sets (`masks.d/`, `blocks.d/`) use the same format and document their
own deviations in their `README.md`.
