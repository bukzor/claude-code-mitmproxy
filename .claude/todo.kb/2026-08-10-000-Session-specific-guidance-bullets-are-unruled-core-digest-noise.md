---
managed-by: Skill(llm-subtask)
status: open
required-reading:
    - blocks.d/README.md
    - keying.claims.kb/this-proxy.kb/block-spans-are-disjoint.md
    - keying.claims.kb/this-proxy.kb/no-hole-may-cross-a-blank-line.md
    - design/040-design.kb/fixture-lifecycle.md
cost-benefit-sweh:
    timebox:
        "@value": 1
        rationale: >-
            The rules themselves are minutes of copying. The hour is the
            design call in "Open question" below; picking wrong costs a
            rewrite of every form.
        confidence: tentative
    benefit-2w:
        "@value": 0.5
        rationale: >-
            Collapses at least three unpromoted cores onto promoted ones,
            so the next survey has three fewer rows to hand-diff. Recurring.
        confidence: tentative
---

# `# Session-specific guidance` bullets are unruled core-digest noise

**Priority:** Medium — the survey is currently reporting false "new prompt
text" at the newest build.
**Complexity:** Moderate — two rules' worth of content, one real design call.
**Context:** Found 2026-08-10 while running the standing promotion survey.

## Problem Statement

`# Session-specific guidance` is a list section whose items are switched on
per session, and only three of its five observed items have `blocks.d/`
rules (`bang-prefix`, `agent-tool-delegation`, `agent-tool-explore`). The
other two are unruled, so they reach the core digest and split captures that
carry identical prompt copy.

The decisive evidence is a single build. `v2.1.226.872` fable produced two
captures whose masked bodies differ by exactly one line -- the skill-
invocation bullet -- and they land on different cores (`6d925e39d43a`,
`64d5cd7cf412`), only one of which is promoted. The survey therefore says
"upstream shipped new text" about a session toggle.

Measured over the 55 masked captures on disk:

| item | rule | bodies |
|---|---|---|
| ``When the user types `/<skill-name>`, invoke it via Skill`` | none | 46 |
| ``the `!` prefix runs the command in this session`` | `bang-prefix.md` | 39 |
| `Calling Agent with subagent_type: "fork"` | none | 13 |
| `Use the Agent tool with specialized agents` | `agent-tool-delegation.md` | 6 |
| `For broad codebase exploration or research` | `agent-tool-explore.md` | 6 |

50 of 55 bodies carry the section at all; 5 carry no section.

## Open question: what happens to the heading

A per-item rule for each of the five leaves the heading behind. A body
carrying only session-optional items strips to `# Session-specific
guidance` followed by a blank line, which is not what a session with none
of them sent -- that body has no section. So per-item rules alone break the
byte-for-byte promise in `blocks.d/README.md`.

Three ways out, none free:

1. **Whole-section forms**, as `git-status` / `git-status-with-user`
   already do. Five combinations are observed today (`bang,skill` x22;
   `bang,skill,fork` x13; `skill,delegation,explore` x6; `skill` x5;
   `bang` x4), so five files would cover the corpus. Cost: the form set is
   the powerset in the limit, and a sixth item doubles it. Also the forms
   must take the *trailing* blank line rather than the leading one, against
   the convention in `blocks.d/README.md`, because with the leading
   separator a shorter bullet list is a literal prefix of a longer one --
   `check_laws.py` would fail on the overlap, which is the good outcome but
   still a dead end.
2. **Per-item rules plus a bare-heading rule.** Smallest by far, and it is
   the only option that does not grow with the item count. It requires the
   heading rule to run after the item rules and to match only what they
   leave behind, which contradicts "no rule may *depend* on an earlier rule
   having fired". Taking it means weakening that invariant from order-free
   to confluent, and saying so in `blocks.d/README.md` and in `DISJOINT`.
3. **Leave the heading in every body.** The five section-less bodies then
   never share a core with the rest. Cheapest to write and the only option
   that keeps every current invariant, at the price of a permanent
   two-population split in the survey.

Recommendation is (2): the invariant it weakens is a means, and the end it
serves -- a stripped body that does not depend on load order -- survives
confluence intact. But this is a ruling, not a detail.

## Acceptance

- [ ] Decide the heading question above.
- [ ] Rules written; `python3 check_laws.py` clean.
- [ ] `python3 survey_captures.py` shows `6d925e39d43a` collapsed onto
      `64d5cd7cf412`, and the two `2.1.226.167` fable rows onto one core.
- [ ] `blocks.d/README.md` updated if the invariant moved.
