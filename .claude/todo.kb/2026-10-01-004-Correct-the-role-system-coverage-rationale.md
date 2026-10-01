---
managed-by: Skill(llm-subtask)
status: ready
---

# Correct the role-system coverage rationale

**Priority:** high -- a false premise in a doc two live sessions consult to make
coverage decisions about this very locus
**Complexity:** low for the correction, open for the policy question
**Context:** measured 2026-10-01 while auditing
`~/.config/claude-mitmproxy/system-message.d/retune-auto-mode-bash-steer`. This
file is self-contained.

## Problem Statement

`design/040-design.kb/prompt-loci-coverage.md` spares `<system-reminder>`
envelopes in user messages **by policy**, on the ground that "their bulk is the
user's own CLAUDE.md/agents/skills content, already under user control". It then
justifies patching `messages[]` entries with `role: "system"` with the claim that
"none of this text is the user's."

That claim is false. Measured over one day of traffic, 787 `role: "system"`
messages classified by opener:

```
  291 (37.0%)  idle nudge ("The user hasn't heard from you in a while")
  115 (14.6%)  <system-reminder> payloads
  100 (12.7%)  environment block
   83 (10.5%)  the USER's own CLAUDE.md, injected as "Contents of <path>:"
   50 ( 6.4%)  compaction recap (prior tool calls re-serialized as prose)
   38 ( 4.8%)  date notices
   29 ( 3.7%)  skills / agents listings
   27 ( 3.4%)  "## Exited Plan Mode"   <- where the auto-mode bulletin rides
   27 ( 3.4%)  file-changed notices
```

Over a third of the locus is the user's own content or conversation content: the
user's CLAUDE.md files, system-reminder payloads, skills and agents listings, and
compaction recaps. Three of those four are precisely the categories the same
document spares at the other address. The same bytes are spared at one locus and
patched at another, on a rationale that does not hold.

Nothing has gone wrong yet only because no rule happens to match them.

## Current Situation

`message_patches.patch_system_messages` walks every `role: "system"` entry
indiscriminately and applies the full rule set to each.

Live tool results are **not** at risk and never were: they ride as `tool_result`
content blocks in `role: "user"` messages, 7604 of them in the measured day,
paired 1:1 with `assistant`/`tool_use` blocks, and nothing patches `role: "user"`.
The only route by which tool output reaches a patchable surface is the compaction
recap, where Claude Code re-serializes prior tool calls and their results as prose
into a `role: "system"` message near the head of the list (observed at `idx=3/28`,
`idx=4/147`).

## Proposed Solution

Two parts, and the second is a judgment call rather than a correction.

1. **Fix the stated rationale.** Replace "none of this text is the user's" with
   what is actually true: the locus is mixed, and what justifies patching it is
   the specific text the rules target (Claude Code's own mid-conversation
   instruction -- plan-mode transitions, the auto-mode bash-first steer), not a
   blanket property of the address.

2. **Decide whether the walk should spare the user's content.** Consistency with
   the policy at the other locus argues yes. The obstacle is that an opener-based
   blocklist cannot work: replays, user content and bulletins are structurally
   identical (bare string or text-block list, no distinguishing keys, confirmed by
   inspection), and **composite messages exist** -- one real example from the
   measured day carries skill descriptions followed by a live relaxed steer, so
   blocklisting the skills opener would skip a genuine target.

   That is an argument for region granularity rather than message granularity,
   which is what `2026-10-01-005-Scope-search-to-the-match-span.md` provides. If
   that lands, this item may reduce to the doc correction alone.

## Implementation Steps

- [ ] Correct the rationale in `design/040-design.kb/prompt-loci-coverage.md`.
- [ ] Carry the same correction into `CLAUDE.kb/system-prompt-loci.md`, whose
      "How `role: \"system\"` messages work" section describes the locus as
      "Claude Code's own instruction" without noting the mixed content.
- [ ] Rule on part 2: spare the user's content in the walk, or accept the mix and
      rely on each rule's own scoping. Record the ruling where the policy lives.
- [ ] If sparing: do it at region granularity, not by message classification, and
      state why in the design note so the composite case is not rediscovered.

## Open Questions

1. Is the policy that spares `<system-reminder>` envelopes a statement about
   *ownership* (never touch the user's bytes) or about *need* (no bloat there
   worth stripping)? The first makes part 2 obligatory; the second makes it
   optional. The doc's wording supports the first reading.
2. Does the compaction recap deserve separate treatment? It is conversation
   content rather than the user's, and it is the one class through which tool
   output becomes patchable.

## Success Criteria

- [ ] No document claims the locus carries nothing of the user's.
- [ ] The decision on part 2 is recorded with its reasoning, including why
      message-level classification was rejected.

## Notes

The measurement is one probe over `log/traffic/2026-10-01.jsonl`: for each
`role: "system"` message, classify by the first line of its text. Re-running it on
a later day is cheap and worth doing before acting, since the proportions will
drift.

**Read `CLAUDE.kb/traffic-log-records-post-patch-text.md` first** if any part of
this involves reading `log/traffic/`. That log is written downstream of the patch
addons, so every record is what we sent, not what Claude Code sent, and two
sessions have already drawn a false conclusion from it.
