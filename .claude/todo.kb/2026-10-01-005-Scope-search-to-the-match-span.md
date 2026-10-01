---
managed-by: Skill(llm-subtask)
status: ready
---

# Scope search to the match span

**Priority:** medium -- closes the last silent path of its class; no known live
occurrence yet
**Complexity:** low change, repo-wide blast radius, so the measurement is the work
**Context:** found 2026-10-01 while auditing
`~/.config/claude-mitmproxy/system-message.d/retune-auto-mode-bash-steer`, and
deliberately left out of
`2026-10-01-000-Anchor-patch-templates-to-line-boundaries.md`. Self-contained.

## Problem Statement

`rule_templates.apply_rules` resolves a rule in two independent passes:

```python
m = first_hit(text, rule.matches)        # are we in scope?
target = first_hit(text, rule.search)    # whole body, from byte zero
```

`search` does not know where `match` landed. So `match` establishes scope at one
place in the body and the rewrite can then happen at a different place -- whichever
occurrence comes first.

Demonstrated before line anchoring landed: a single `role: "system"` message
holding a line-numbered copy of `search.d/strict.md` followed by the live
auto-mode envelope produced

```
1	                                     <- quoted copy gutted
While auto mode is active:
Do your work through the Bash tool ...   <- live steer SURVIVED
misses: []                               <- silent
```

Three failures at once: the transcript is corrupted, the target rides through
unpatched, and nothing is loud.

## Current Situation

Line anchoring (`2026-10-01-000`, landed) closed the numbered half. Anchored
`search` templates no longer match `1\tDo your work ...`, because the body is
preceded by a tab rather than a newline; the measured composite case flipped from
"deletes the quoted copy" to "deletes the live steer".

What remains open is an **unnumbered verbatim quote** -- a `cat` or `sed -n` of a
rule file replayed into a `role: "system"` message, or the same flattened into a
compaction recap. There the body sits at a genuine line start in both copies, so
anchoring cannot discriminate and leftmost still wins.

Reachability is not negligible, and the reason is circular in a way worth noting:
the steer being deleted is itself an instruction to read files with `cat`, `head`
and `sed -n` rather than Read. A session that complies produces exactly the
unnumbered form, on exactly the files that define the rule.

## Proposed Solution

Prefer a `search` hit inside the `match` span, falling back to whole-body:

```python
target = (first_hit_within(text, rule.search, m.start(), m.end())
          or first_hit(text, rule.search))
```

**Implementation trap, record it before writing the code:** use
`pattern.search(text, pos, endpos)`, never `text[m.start():m.end()]`. Slicing makes
`\A` match at the slice boundary, which re-admits a mid-line match and silently
undoes the anchoring from `2026-10-01-000`. With `pos`/`endpos`, `\A` keeps meaning
true string start and the `(?<=\n)` lookbehind can still see across `pos`, which is
what makes an anchored template match correctly inside a span.

Why the fallback: prompt-locus rules legitimately rely on the independence -- match
a stable section heading or shape marker near the top, search a paragraph far
below. Removing it outright would break them. The fallback keeps every current
behavior reachable, so nothing gets worse than today.

## Why region granularity rather than excluding replays

The alternative fix is to stop the walk from offering replayed content to the
rules at all. That was investigated and rejected:

- Replays, user content and bulletins are structurally identical in the request:
  `content` is a bare string or a list of `text` blocks, with no distinguishing
  keys. Classification can only be opener text.
- **Composite messages exist.** One real example from 2026-10-01 carries skill
  descriptions followed by a live relaxed steer in a single message. Any
  message-level exclusion that caught the skills opener would skip a genuine
  target.

Confining the rewrite to the span the rule actually recognized handles a mixed
message correctly without classifying it: the live bulletin's span is patched, the
quoted region never enters consideration, and it does not matter that they share a
message. See `2026-10-01-004-Correct-the-role-system-coverage-rationale.md`, which
reaches the same conclusion from the policy side.

## Implementation Steps

- [ ] Write the failing test first: one `role: "system"` message with an
      unnumbered verbatim copy of an arm ahead of the live envelope. It must end
      with the live steer deleted and the quoted copy byte-identical.
- [ ] Add the in-span-first preference to `apply_rules`, with `pos`/`endpos`.
- [ ] Measure the blast radius across all 77 templates and the 44 fixtures in
      `system-prompts.kb/`: for every rule, does the chosen target move? Any rule
      whose target moves needs its README read before accepting the change.
- [ ] Full suite plus `monitoring/`, then pre-commit.
- [ ] Document the semantics in the dialect README beside the `match` vs `search`
      section: scope is established anywhere, the rewrite prefers the scoped
      region.

## Open Questions

1. Should the whole-body fallback be loud? A rule that finds its target only
   outside its own match span is working, but not in the way its author probably
   meant. A one-time report per rule would surface the prompt-locus rules that
   genuinely depend on independence, and might argue for widening their `match`
   instead of keeping the fallback forever.
2. Residual, narrower than today and not addressed here: a reworded live target
   coexisting with an old-wording quote would still fall back and gut the quote
   silently.

## Success Criteria

- [ ] Unnumbered-quote test: live target deleted, quoted copy untouched.
- [ ] No rule's chosen target moves across the 44 fixtures without a recorded
      reason.
- [ ] Suite, `monitoring/` and pre-commit green.

## Notes

Do not reach for `log/traffic/` to judge whether this has fired in production
without reading `CLAUDE.kb/traffic-log-records-post-patch-text.md` first: the log
is written downstream of the patch addons, so a gutted quote in it is evidence of
the bug while an intact one proves nothing about the input.
