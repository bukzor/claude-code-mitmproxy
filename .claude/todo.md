---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [ ] <https:../proxy-memory-leak-2026-08-18/todo.kb/2026-08-18-000-confirm-store-retention-and-adopt-a-bound.md>
      (outside `.claude/`, so this breadcrumb is its only sweep visibility):
      restart the proxy once so `quietconn.py` loads; next day, capture
      RSS as fix verification; then rule on standing RSS monitoring.
- [x] <https:todo.kb/2026-08-09-000-Masks-as-template-rules--quotient-session-noise-from-capture-digests.md>
- [x] <https:todo.kb/2026-08-10-000-Session-specific-guidance-bullets-are-unruled-core-digest-noise.md>
- [x] Promote a `long-form` fixture at v2.1.226. Done — the haiku
      capture, unsuffixed, once `masks.d/knowledge-cutoff.md` proved
      haiku and sonnet long-form are the same copy (their v2.1.215 cores
      differed by that one line and nothing else).
- [x] Split every check into data / rendering / properties, per
      `check_verdict.py`: `collect()` gathers, `render()` formats, `PREDICATES`
      judges. The command prints both halves and exits 2 when a predicate
      found something; `monitoring/test_checks.py` asserts the same
      function objects, parametrized over `CHECKS × PREDICATES`, so there
      is no per-check test file to keep in sync. It paid for itself
      immediately: `check_dark_patches.py` could finally assert
      subsumption, which found `strip-help-feedback` matching on the
      heading `# Doing tasks` that `strip-doing-tasks-bloat` deletes
      first — dead for as long as both have existed, with its target
      text SURVIVING into every long-form session. Its `match.md` now
      names its own target (the idiom `strip-additional-dirs` already
      used), which is order-independent; the set strips 232 more chars
      and the long-form floor rose 2435 → 2551.
- [x] Move the directly-importable modules out of the repo root — into a
      real package, `lib/claude_mitmproxy/`, rather than the bare
      `sys.path` entry first sketched here. Bareness bought nothing:
      mitmproxy registers a path-loaded addon as
      `__mitmproxy_script__.<stem>`, so the addon copy is never the
      imported copy whatever the layout, and the pairing (mitmproxy
      re-executes the addon, `reload.py` re-executes the library) only
      needs every importer to agree on one name. A package makes that
      name unambiguous and gives the console scripts a real target.
      `repo_paths.py` holds `ROOT`/`LOG`, replacing nine `__file__` anchors
      that would each have needed re-counting; `proxy.sh` and
      `flow2jsonl.sh` export `PYTHONPATH=lib`, which the compressor
      subprocess inherits (now spawned `-m
      claude_mitmproxy.compress_traffic`).
- [x] Give the modules names that say what they hold, and separate the
      addons from everything else. `paths`/`templates`/`shapes`/`corpus`/
      `verdict` were abstract enough to name anything, and became
      `repo_paths`/`rule_templates`/`prompt_shape`/`prompt_corpus`/
      `check_verdict`. The addons were worse than abstract: nothing
      distinguished `syscapture.py` (six mitmproxy hooks) from
      `survey_captures.py` (a report), so they moved to `addons/`, which
      now holds exactly the files `proxy.sh` `-s`-loads. That directory
      only means something if the rule holds in both directions, so the
      three addons that carried library code were split — the hooks stayed
      in `addons/`, `prompt_location` / `prompt_patches` /
      `prompt_capture` / `tool_patches` took the rest — and `reload.py`
      asserts nothing outside `addons/` imports one. The split found its
      own simplification: `syscapture` never wanted `syspatch`, only the
      locator. `diff_matrices.py` now parses back into the
      `PatchMatrix` its producer emits, so the diff compares data rather
      than aligned text; `tests/test_matrix_format.py` holds
      `parse(render(m)) == m`.
- [ ] Reconcile `v2.1.226.md`'s tools bullet when a sonnet long-form
      capture at that version shows up. The promoted body says "Prefer
      dedicated tools over PowerShell ... (Read, Edit, Write, Glob,
      Grep)" while its own `# Environment` says `Shell: bash`, and all 20
      other captures on disk say Bash and list only Read/Edit/Write.
      Either upstream A/B'd a reworded bullet with the shell name
      mis-substituted, or the rewording is real and the shell name is a
      bug. A second 2.1.226 long-form capture settles it; until then the
      fixture carries a sample of one.
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
