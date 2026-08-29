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
- [ ] Add `blocks.d/` rules for the two session-optional blocks nothing
      covers: the auto-mode paragraph ("You are operating autonomously. The
      user is not watching in real time...", through the check-your-last-
      paragraph and check-the-evidence bullets) and the model-identity
      paragraph ("This iteration of Claude is Claude Fable 5..."). 36 of 99
      captures carry each; no `blocks.d/` or `masks.d/` rule matches either
      (`grep -rl 'operating autonomously\|iteration of Claude' blocks.d/
      masks.d/` is empty). Both are session/model state, not prompt copy, so
      leaving them in inflates every carrier's core -- two captures of one
      copy read as two copies -- and inflates that shape's `_strip-rate`
      floor, the hazard CLAUDE.md already names. Found via
      `survey_captures.py --drift`; diffing the two 2.1.251 harness-fable
      cores is the reproduction. Run `check_laws.py` and
      `check_strip_floors.py` with the edit, then re-check `--drift`: some
      of today's 22 uncovered copies should merge.
- [ ] Rule on how to promote two *concurrent* copies of one shape at one
      cc_version. `harness-fable` at 2.1.251 has two (`ada19cdbceea` from
      2.1.251.d59, `6ee2dac2d820` from 2.1.251.171) differing on a reworded
      `<system-reminder>` harness bullet -- genuine copy drift, so the
      `blocks.d/` fix above will not merge them. `system-prompts.kb/CLAUDE.md`
      names variants per *shape* (`-opus`, `-fable`), which has no slot for
      two copies of the same shape at the same version. Either pick one
      (which one, on what rule?) or extend the naming.
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

## Later

- [ ] Decide whether `survey_captures.py --drift` should become a loud
      `check_*` instead of a report someone remembers to run. It is the last
      standing duty with no tripwire, which `design/020-goals.kb/earned-silence.md`
      argues against on principle. The predicate cannot be "any uncovered
      copy" — 23 are uncovered today, most of them historical, so it would be
      permanently red. "The newest copy per shape is uncovered" self-clears on
      promotion and is the actual duty, but it goes red the moment upstream
      ships anything, which is either the point or a nag depending on how
      often that is. Needs a ruling, not an implementation.
- [ ] Consider renaming this repo to encompass both works -- the proxy and
      `binpatch.py` (on-disk patches). The two-surface framing already landed in
      README + CLAUDE.md, so what's left is mechanical: the name is carried by
      the repo dir, the git remote (`claude-code-mitmproxy`), pyproject
      `name`/`description`, the package `claude_mitmproxy` (dir + every import +
      `claude-mitmproxy-*` script), the README h1, and CLAUDE.md's lead; plus two
      external references -- the `~/.claude/settings.json` SessionStart hook path
      and the `~/.claude/{system-prompt,tool-description}-patches.d/README.md`
      that cite `~/claude/mitmproxy/`. `grep -rwin mitmproxy` scopes it.
- [ ] Finish weaving binpatch into `design/`'s why-chain. The sharpest
      contradiction is already reconciled --
      `020-goals.kb/decoupled-from-the-cli.md` now records binpatch as the
      deliberate exception for behavior unreachable on the wire. Still open:
      `010-mission.kb/final-say-over-injected-behavior.md` is wire-centric
      ("the text it injects into every request"; "CLI upgrades require no
      rework beyond re-verifying targets") -- true of the proxy surface, but
      the binpatch surface re-applies per upgrade, so the mission's scope and
      that success criterion want a one-line caveat. Then decide whether
      binpatch earns its own `020-goals.kb/` and/or `040-design.kb/` node, or
      stays a documented exception on the decoupling goal alone.
