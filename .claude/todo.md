---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [x] <https:todo.kb/2026-08-09-000-Masks-as-template-rules--quotient-session-noise-from-capture-digests.md>
- [x] <https:todo.kb/2026-08-10-000-Session-specific-guidance-bullets-are-unruled-core-digest-noise.md>
- [ ] Promote a `long-form` fixture at v2.1.226 — newest promoted is
      `v2.1.223`, and the only 2.1.226 long-form capture
      (`751d9ae396cb`, haiku) matches no fixture core.
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
