---
managed-by: Skill(llm-subtask)
---
# Todo

- [ ] Promote v2.1.207 captures into `system-prompts.kb/` (backlog found
  2026-07-12 review; kb newest is v2.1.202/203-harness)
  - [x] `cp` newest long-form raw capture
    (`prompt-captures/v2.1.207.a42_claude-sonnet-5_*.raw.md` →
    `v2.1.207.md`) and newest harness — a newer fable capture
    (`v2.1.207.c82_claude-fable-5_*.raw.md`, 2026-07-12) landed after the
    review that wrote this todo, so it (not `.468_`) went to
    `v2.1.207-harness.md`
  - [x] Run `check_patches.py` (both, zero warnings confirmed) and
    `check_dark_patches.py` (table clean, no unexpected MISS)
  - [ ] Then the additive-drift bloat review applies to these, not
    v2.1.202: see `ideas.kb/2026-07-08-000-Review-v2-1-202-*` (idea file
    retargeted to v2.1.207 2026-07-12; review itself not yet done)
- [ ] Add standing-maintenance bullet to root `CLAUDE.md`: check
  `prompt-captures/` for cc_versions newer than the newest kb capture
  (promotion currently has no trigger; additive drift is invisible to
  every loud mechanism)
- [ ] `check_dark_patches.py`: flag subsumption — evaluate each `match`
  against text-as-patched-by-earlier-patches too; raw-HIT but
  patched-MISS = SUBSUMED (the `strip-over-engineering` failure mode is
  still audit-only)
- [ ] `load_patches`/`load_tool_patches`: assert on malformed patch dirs
  instead of silently skipping (missing `match.*`/`description.md` is a
  config error, not out-of-scope — unearned silence)
- [ ] Decide subagent-prompt coverage: `is_subagent_request` passes Task-tool
  prompts through unpatched *and uncaptured*, and no design doc records
  that as a decision — either add the by-policy sentence to
  `design/040-design.kb/prompt-loci-coverage.md` or treat as a new locus
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
