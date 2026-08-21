---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [ ] <https:../proxy-memory-leak-2026-08-18/todo.kb/2026-08-18-000-confirm-store-retention-and-adopt-a-bound.md>
      (outside `.claude/`, so this breadcrumb is its only sweep visibility):
      restart done, fix-verification RSS capture done 2026-08-21 (99 MiB →
      141 MiB / ~66.6 h, ~30x slower than the pre-fix leak) — only the
      standing-RSS-monitoring ruling is left, open question for the user.
- [ ] Reconcile `v2.1.226.md`'s tools bullet when a sonnet long-form
      capture at that version shows up. The promoted body says "Prefer
      dedicated tools over PowerShell ... (Read, Edit, Write, Glob,
      Grep)" while its own `# Environment` says `Shell: bash`, and all 20
      other captures on disk say Bash and list only Read/Edit/Write.
      Either upstream A/B'd a reworded bullet with the shell name
      mis-substituted, or the rewording is real and the shell name is a
      bug. A second 2.1.226 long-form capture settles it; until then the
      fixture carries a sample of one.
- [ ] Confirm the v2.1.237 shape convergence with a second capture per
      model. `system-prompts.kb/v2.1.237-opus.md` is a fable-5 session
      carrying the `-opus` shape verbatim (`# Delivering work`, but no
      `# Corrections` — present in every prior `-opus` fixture) and
      `system-prompts.kb/v2.1.237.md` is a sonnet-5 long-form session with
      neither `# Delivering work` nor `# Corrections` (present in
      v2.1.233's long-form). Each is a sample of one: could be a genuine
      version-level shift (fable folded into `-opus` outright, sonnet
      reverted the v2.1.233 merge) or per-session variance (e.g.
      `# Corrections` is itself session-optional, not static). A second
      capture per model at >=2.1.237 settles it; until then
      `condense-corrections` silently not firing on either new fixture is
      expected, not a regression (`check_dark_patches.py` confirms).
      `system-prompts.kb/CLAUDE.md`'s naming section already documents
      that shape and model decoupled as of this version.
- [x] Decide whether `git-status` should strip a commit-less repo. Yes,
      and the fix was one character: `$LINES` now matches zero or more
      lines. The miss was never in `blocks.d/git-status.md` — its
      `$GITLOG` is a DEFAULT hole — but in `masks.d/git-log.md`, whose
      `$GITLOGLINES` could not match the empty region a fresh repo sends.
      Not a third hole type, just the same one with its count relaxed; the
      blank-line bound is untouched, and writing the placeholder's name in
      where nothing was is the coarsening masks want. All five checkers
      byte-identical except the survey, which gained four rows: cores
      27 → 23, unpromoted 21 → 17.
