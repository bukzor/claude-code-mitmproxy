---
managed-by: Skill(llm-subtask)
status: todo
---

# Assert patch-rule-set idempotence

**Priority:** medium -- a demonstrated 27% violation rate, fixed but unguarded
**Complexity:** small -- one predicate plus a discovery in an existing
`collect()`; roughly 30 lines
**Context:** 2026-10-01. Blocked on the trailing-newline convention
(`2026-10-01-000`, follow-on section), which changes what a template matches.
This file is self-contained; no prior session context is needed.

> [!DRAFT] agent-authored 2026-10-01, vetoable. The operator asked for the
> analysis to be filed rather than built, since the files it touches were being
> rewritten concurrently. Nothing here is ratified.

## Problem Statement

Applying a rule set twice must equal applying it once. On a locus that persists
in conversation history -- `messages[]` entries with `role: "system"` -- a
non-fixpoint re-forks the cached prefix on every turn; on the prompt body it
simply means the patched text is not stable.

Nothing asserts it for patches. `check_laws.not_idempotent` covers `masks.d/`
only, and `check_laws.collect()` does not load the patch rule sets at all.

**It was violated, recently, in the real data.** Measured on 2026-10-01 against
the then-committed `template_to_regex`: **65 of 240 bodies on disk were not
idempotent**, each growing about 90 bytes on the second pass -- a rule whose
replacement output re-matched its own search. The anchoring work
(`2026-10-01-000`) took that to zero.

So the law has a demonstrated violation, a fix, and no guard. The 66th will be
as quiet as the first 65 were. It was found by hand, incidentally, while
auditing a different problem.

## Why this is the only patch law worth a predicate

Sorting the candidates by whether they are contingent on the rule data or
theorems of the code. This is the analysis the task exists to preserve: a
matrix of laws across subjects was proposed and dropped, because most cells
cannot fail.

| candidate                    | verdict                                           |
| ---------------------------- | ------------------------------------------------- |
| idempotence                  | **contingent** -- 65 live violations; no predicate |
| masks only coarsen           | **contingent** -- predicate exists                 |
| block spans disjoint         | **contingent** -- predicate exists                 |
| a deletion shrinks the body  | theorem: `replace == ""` makes the replacement `""`, so the span change is exactly `-(end - start)` |
| determinism                  | theorem: sorted loads, pure functions             |
| inert off-target             | theorem: `apply_rules` continues on a match miss  |
| loud on half-apply           | theorem: the code appends the `Miss`              |
| JSON shape preserved         | theorem of the walk; an ordinary unit test at most |

Three are contingent and two of those already have predicates. A declaration
framework over the other five would have generated waiver text for properties
that cannot fail -- so do not rebuild it. The generic property wanted from such
a framework comes instead from the quantifier being discovered rather than
listed, below.

## Proposed Solution

1. **`check_laws.collect()` discovers rule directories** instead of naming
   `masks.d/` and `blocks.d/` by hand. The key already used by
   `check_verdict.all_checks()` fits: module-level `*_DIR` constants whose value
   names a `.d` directory. Those are exactly the five rule sets --
   `masks.d/`, `blocks.d/`, `system-prompt.d/`, `system-message.d/`,
   `tool-description.d/` -- and nothing else. A sixth locus then falls under the
   law the moment it exists, with nothing to register anywhere. That is the
   whole of the "cannot forget" requirement.
2. **One predicate**, `not_idempotent_patches`, returning the bodies whose
   second application differs from the first, grouped by rule set. Use
   `rule_templates.apply_rules` directly rather than
   `prompt_patches.apply_patches`: it reports misses by return value and files
   no incident, so a check run cannot queue work for a human.
3. `monitoring/` and the `claude-mitmproxy-check-laws` command pick it up with
   nothing further to wire, and the hook already fires on `masks.d/`,
   `blocks.d/` and `system-prompts.kb/` edits.

## Blocked on, and why

The trailing-newline convention (`2026-10-01-000`, follow-on) changes what a
template matches at its right edge and introduces "a deletion consumes one
following newline". Both change the fixpoint. A predicate written first would
measure a world about to be replaced, and it edits `check_laws.py`,
`rule_templates.py` and `prompt_patches.py` -- the same files that work is
rewriting. Land the convention, then this.

Re-measure after the convention lands rather than trusting the 65 figure: it
was taken against the pre-anchoring compiler and is a historical fact about
that state, not a prediction.

## Open Questions

1. **Does `tool-description.d/` belong under this law?** It is exact-compare,
   not templates: `apply_tool_patches` replaces a whole description. Applying
   it twice is trivially idempotent if the stub does not itself match upstream,
   and that is worth asserting once rather than per body. Possibly a different
   predicate, possibly out of scope.
2. **Which corpus?** `check_laws.Corpus.bodies` is captures plus fixtures, ~240
   on disk. Captures live under `log/` and are not version-controlled, so a
   fresh checkout sees fewer; `monitoring/`'s `REQUIRES` is where that
   difference is written down, and this predicate will need an entry if it
   quantifies over captures.
3. **Should the message locus be included before it has captures?** There is no
   pristine capture for `role: "system"` bulletins, so the only bodies to
   quantify over are synthetic. Probably wait for that capture work rather than
   asserting over an empty set, which would read as a pass.

## Success Criteria

- [ ] `check_laws.collect()` names no rule directory by hand.
- [ ] A rule set added in a new directory is covered with no edit to
      `check_laws.py`, demonstrated by planting one.
- [ ] `not_idempotent_patches` reports zero against the current data, and a
      planted self-matching `replace.md` is caught and names the rule.
- [ ] No incident is filed by a check run.
- [ ] Full suite and `monitoring/` green; pre-commit green.
