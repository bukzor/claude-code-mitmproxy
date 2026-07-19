---
managed-by: Skill(llm-subtask)
---
# Todo

(2026-07-19 gc: 8 resolved items cleared — each verified against a git
log commit, disposition recorded there, not repeated here. Newest:
`33e0d07` regular maintenance, `6be04df`/`975f9c4`/`01115ff`
subagent-prompt-coverage, `151e6f5`, `eb9e1d0`/`6a7d2ab`, `12c598c`,
`b68c598`.)

- [ ] Decide `system.patched.md`'s fate: tracked but v2.1.76-era stale;
  regenerable, so delete (with matching `NOTICE`/README license edits) or
  regenerate with a stated purpose
- [ ] Trivia from 2026-07-12 review
  - [ ] `apply_patches` appends a trailing newline even when no patch
    applies — unpatched bodies differ from stock by one byte
  - [ ] `flow2jsonl.sh` uses `tail -f` (never exits at EOF); README says
    "replay" — fix whichever is wrong
  - [ ] syspatch README testing example references defunct `system.md`
    naming
- [ ] Decide `jsonl2sysprompt.sh`'s fate: its kb-capture job moved to
  `syscapture.py` (and its output is post-patch contaminated); keep as a
  jsonl-archaeology utility, or delete it and its README entry.
