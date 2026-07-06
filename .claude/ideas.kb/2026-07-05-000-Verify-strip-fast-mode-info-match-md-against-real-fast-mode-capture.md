---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.5
    rationale: |
      Toggle /fast in a proxied session, capture via traffic.jsonl,
      compare the <fast_mode_info> tag wording, re-target match.md if
      drifted. Mechanical once a fast-mode session happens.
  benefit-2w:
    "@value": 0.1
    rationale: |
      User doesn't use /fast; the patch only fires on fast-mode
      sessions, so a dark patch here has no day-to-day cost.
---

# Verify strip-fast-mode-info match.md against real fast-mode capture

## The Idea

`strip-fast-mode-info`'s `match.md` targets a `<fast_mode_info>` tag
reading "uses the same Claude Opus 4.6 model", but the *unconditional*
Fast Mode line elsewhere in the current prompt already says
"Opus 4.8/4.7" -- the same stale-version smell `strip-over-engineering`
had before it was found to be silently dark. See
`~/.claude/system-prompt-patches.d/strip-fast-mode-info/README.md`.

## Open Questions / Unknowns

- Has the tag wording drifted (patch silently dark), or does the tag
  only ever render with the old wording it was captured from?

## Next Steps (if pursuing)

- [ ] Toggle `/fast` in a proxied session, capture via `traffic.jsonl`
- [ ] Compare the tag's current wording; re-target `match.md` / add
  `search.d/` if it drifted

## Lifecycle

**Status:** Exploring -- punted indefinitely 2026-07-05 (user doesn't
use /fast; accepted risk: the patch may be silently dark until then).
Demoted from `todo.md`.
