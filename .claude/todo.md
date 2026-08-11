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
- [ ] Decide whether `git-status` should strip a commit-less repo. Both
      `2.1.226.167` fable captures (core `749564b55c22`, the last
      unpromoted 2.1.226 row) end `Recent commits:\n` with nothing after,
      so `$GITLOG` — a `$LINES` hole, which needs at least one line —
      cannot match and the whole block reaches the core digest. Working as
      designed: under-deletion is loud. But it recurs in every fresh repo.
  - [ ] A third whole form is *not* available: `...Recent commits:\n` is a
        literal prefix of the with-commits form, so both would match a
        body that has commits and `check_laws.py` would fail on the
        overlap — the hazard `blocks.d/README.md` warns about.
  - [ ] The only mechanism that works is a hole matching zero or more
        lines. Still blank-line-bounded, so `BOUNDED_HOLES` is satisfied,
        but it contradicts "two hole types and no third"
        (`design/040-design.kb/template-patch-model.md`) and is wrong for
        `masks.d/`, where an empty match would write the placeholder's own
        name in where there was nothing.
  - [ ] Cheapest honest alternative: accept one permanently unmatched core
        and say so in `blocks.d/README.md`.
