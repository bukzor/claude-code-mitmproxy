---
managed-by: Skill(llm-subtask)
status: done
closeout: >-
    Both tiers landed 2026-08-09 in ~3.5 SWEh: `masks.d/` (13 rules) +
    `check_masks.py` for tier 1, `blocks.d/` (11 rules) + the survey `core`
    column for tier 2, on a `rule_templates.py` extracted from `prompt_patches.py`.
    See "Outcome" below for two corrections to the criteria as written.
required-reading:
    - design/040-design.kb/content-addressed-capture.md
    - design/040-design.kb/template-patch-model.md
    - design/020-goals.kb/pristine-fixture-supply.md
    - ~/.claude/system-prompt-patches.d/README.md
cost-benefit-sweh:
    timebox:
        "@value": 4
        rationale: >-
            Engine extraction + ~8 rule files + checker wiring + doc updates.
            Beyond 4h the remaining value is tier 2 (survey core digest),
            which can ship separately.
        confidence: tentative
    benefit-2w:
        "@value": 1.5
        rationale: >-
            The 2026-08-09 promotion survey hand-diffed 8 "new" captures to
            conclude zero copy changes (~0.5 SWEh); recurring duty, plus
            masks become offline-validated instead of silently rotting.
        confidence: unsure
---

# Masks as template rules: quotient session noise from capture digests

**Priority:** Medium — recurring survey/promotion friction, no incident pressure
**Complexity:** Moderate — refactor + rule authoring; design already settled
**Context:** Decided 2026-08-09 in conversation after a promotion survey found
8 post-v2.1.221 captures with zero real copy changes — every "new unique
prompt" was session noise.

## Problem Statement

`incidents.content_hash` masks too little, so session-conditional content
mints spurious "unique" captures: additional-working-dirs items, memory /
auto-memory paths, background-job tmp path, and the 1M-context markers
(`[1m]` model-ID suffix, `(1M context)`) all reach the digest. Evidence:
fable `2.1.224.062` differs from the promoted `v2.1.221-fable` body *only*
by `[1m]` + adddirs items; the three 2.1.221 automem sonnet captures differ
mainly by their memory path. Each survey pass then needs hand-diffing to
learn "nothing actually changed."

Separately, `_VOLATILE_SUBS` (incidents.py) is hand-written regex in code
with zero validation: a typo'd mask fails silent-and-open — masking stops,
every session mints new digests, nothing is loud. That is exactly the
additive-drift failure class this project exists to catch.

## Current Situation

- `incidents.py` `_VOLATILE_SUBS`: 4 in-code regexes (gitStatus tail, cwd
  line, scratchpad path, cc_version); `content_hash` = sha256 of the
  substituted text; capture dedup keys on it (`prompt_capture.save_prompt`
  first-seen-wins).
- Template engine (literal templates, `$NAME`/`$LINES` placeholders,
  `match`/`search` split, `match.d/` alternatives) lives in `prompt_patches.py`;
  format spec in `~/.claude/system-prompt-patches.d/README.md`.
- Existing patches already match the volatile regions masking needs:
  `strip-git-status`, `strip-additional-dirs`, `strip-scratchpad-bloat` —
  mask rules can start as near-copies of their match templates.
- `survey_captures.py` surfaces block presence via `BLOCK_MARKERS`
  (shared registry candidate: `prompt_shape.py`).

## Proposed Solution

Two tiers — same rule format, different consumers:

**Tier 1 — volatile *content* → capture digest.** Replace `_VOLATILE_SUBS`
with template-format mask rules (match + replace only; replace holds
canonical `$PLACEHOLDER` tokens). A mask miss is always silent (bodies
include tracebacks and subagent prompts). Rules live **in-repo** (new
`normalize.d/` or similar), not `~/.claude`: patches are user preference,
masks define the capture system's identity function — digests must not
depend on per-machine state.

**Tier 2 — block *presence* → survey view only, never the capture digest.**
First-seen-wins dedup means presence-in-digest would silently discard
fuller variants (breaks "promote the fullest raw per shape" and
`pristine-fixture-supply`), and stripping blocks from the hash blinds
capture to copy changes inside them. Instead: a block-strip rule set
consumed only by `survey_captures.py`, producing a "core digest" column —
rows sharing a core are the same prompt modulo session-optional blocks;
only a new core warrants a hand-diff. Derive `BLOCK_MARKERS` from these
rules' anchors so flags and stripper can't drift.

Layering: extract the template compiler out of `prompt_patches.py` into a shared
module importable by `incidents.py` (no cycle); compile rules once at addon
load so a bad rule kills proxy start loudly instead of breaking hashing
per-request.

## Implementation Steps

- [x] Docs first: update `design/040-design.kb/content-addressed-capture.md`
      (masking mechanism becomes template rules) and
      `template-patch-model.md` (model gains a second consumer)
- [x] Extract template engine from `prompt_patches.py` into a shared module;
      `prompt_patches` behavior unchanged
- [x] Port the 4 `_VOLATILE_SUBS` masks to in-repo rule dirs; delete
      `_VOLATILE_SUBS`. cc_version may need a `$TOKEN`-type placeholder
      (non-whitespace run, `;`-delimited here) — add it to the engine and
      format README if so
- [x] Add tier-1 masks: adddirs items, `# Memory` / auto-memory paths,
      bg-job tmp path, `[1m]` suffix, `(1M context)`
- [x] Wire `incidents.normalize_body` to the compiled rules (load-time
      compilation, fail-fast)
- [x] Mask validation: assert each mask matches the fixtures it should
      (extend `check_patches.py` or sibling checker); a mask matching no
      fixture is loud (dark-mask)
- [x] Regenerate masked `.md` siblings in `log/prompt-captures/` from
      `.raw.md`; move superseded-digest duplicates to `trash/`
- [x] Tier 2: block-strip rule set + core-digest column in
      `survey_captures.py`; derive `BLOCK_MARKERS` from it
- [x] Rerun `check_patches.py`, `check_dark_patches.py`, and
      `survey_captures.py`; confirm post-v2.1.221 captures collapse

## Success Criteria

- [x] `_VOLATILE_SUBS` is gone; all masking flows through template rules
- [x] Recomputing digests over existing raws collapses the known noise
      pairs (e.g. `2.1.224.062` fable ≡ `v2.1.221-fable` fixture body; the
      three 2.1.221 automem sonnet captures ≡ one) — *the second pair is a
      tier-2 criterion, see Outcome*
- [x] A deliberately broken mask is caught offline by the checker, not by
      digest churn in production
- [x] Survey answers "any new prompt copy since the fixtures?" from the
      core-digest column alone, no hand-diffing

## Outcome

Landed as `rule_templates.py` (engine, shared by `prompt_patches.py`, `incidents.py`,
`survey_captures.py`), `masks.d/` + `check_masks.py`, `blocks.d/` + the
survey `core` column, and `rekey_captures.py` for the existing store
(70→46 main captures, 23→21 subagent). Behavior-preservation proved by
diffing `check_patches.py` and `check_dark_patches.py` output against a
HEAD worktree: byte-identical.

The three open questions resolved as: two rule dirs, one per tier
(`masks.d/`, `blocks.d/`); duplicate rather than share templates with the
`~/.claude` strip patches; re-key the store in place, with the caveat that
the proxy must be restarted first or it re-captures every renamed body
under the old scheme.

Two corrections to the plan above:

- **The automem-sonnet criterion was mis-tiered.** Those three captures do
  not collapse under masking and should not: they differ by real prompt
  content (a TaskCreate line, two Agent-tool lines, an "enough information
  to act" paragraph) that varies *within* build 8fd. That makes them
  session-conditional *blocks*, so they collapse at tier 2 instead — all
  three now share core `baa2cb7dd3e2`.
- **`BLOCK_MARKERS` was not derived from the rules; it was dissolved into
  them.** `strip_blocks` returns the names of the rules that fired, so the
  survey's flags *are* the stripper's output and cannot drift from it.

## Notes

Session evidence and the full argument (including why block presence must
stay out of the capture digest) are in the 2026-08-09 conversation; the
digest-relevant facts are restated above so this file stands alone.
`survey_captures.py` gained a `bgjob` BLOCK_MARKER that session
(mitmproxy@37d9bd0) — the `# Background Session` block replaces
`# Scratchpad Directory` in bg-job sessions and is one of the
presence-class toggles tier 2 quotients away.
