---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [ ] Collapse "Standing maintenance" to demand-driven: every polled duty
      becomes loud or event-driven, so the whole section reduces to "triage
      `log/patch-failures/` when nonempty" (2026-08-29 toil evaluation;
      `--drift` itself already landed as deda83e). One small commit per
      subtask, in landing order; each retires a CLAUDE.md duty line, but
      the docs edit waits for the final subtask so the section never
      overstates what's built:
  - [x] `gc_patch_failures.py`: also expire *live* `_uncaught-*` incidents
        past the retention window. Safe by an existing property:
        `save_incident` is idempotent per (rule, content), so a persistent
        cause re-files (and re-warns) after expiry, while a live-edit
        transient never returns. Retires transient triage entirely. Test:
        expired-then-refired incident warns a second time. Landed:
        `expire_transients()`, archiving rather than deleting so `gc` still
        gets its own look and a wrong guess stays readable beside the
        re-filed record; `tests/test_gc_transients.py` (6, each
        mutation-verified). CLAUDE.md's duty line is still accurate as
        written ("run gc occasionally") and retires with subtask 2.
  - [x] Run gc opportunistically at proxy startup (beside the eager
        `masks()` load in `addons/syspatch.py`, or inside
        `archive_incident`). Retires "run gc occasionally". Landed:
        `sweep_at_startup()` from syspatch's load hook — not
        `archive_incident`, which `expire_transients` itself calls, so a
        sweep hung there would run once per record it archived. Failures
        file a `_gc-patch-failures` incident instead of refusing to start.
        Fallout: `gc_patch_failures` was the first library module an addon
        imports that `reload.py`'s RELOADED didn't name, which would have
        left it silently stale under a live proxy; `reload.py` now checks
        that set against the addons' imports (observed red on exactly this).
  - [x] Pre-commit hook: any commit touching `masks.d/`, `blocks.d/`, or
        `system-prompts.kb/` runs the offline check suite (`check_laws`,
        `check_masks`, `check_strip_floors`, `check_patches`,
        `check_dark_patches` — all subsecond). Pure functions of those
        inputs: event-driven makes them impossible to forget and pointless
        to schedule. Retires the "run X after editing Y" duty lines.
        Landed: `.pre-commit-config.yaml` runs `pytest monitoring/`, not the
        five commands by name — monitoring/ already parametrizes over every
        check's PREDICATES, so a property added beside its data gates
        commits with nothing to update here. Verified in all three states
        (skips an unrelated path, passes on clean data, blocks on a
        deliberately dark mask). `pre-commit install` chained the existing
        git-localhost-store hook as `pre-commit.legacy`; README says so,
        since `.git/hooks/` isn't versioned.
  - [ ] Make `--drift` loud (promoted from ## Later, which asked for a
        ruling: the ruling landed as the 2026-08-29 "get us to that state"
        direction; the predicate below is agent-proposed, veto before
        building). Predicate: an unpromoted core that *recurs* (>=2 raw
        captures) per shape — recurrence answers the noted "goes red the
        moment upstream ships anything" objection, since a single fresh
        capture stays silent until a second session confirms the shape
        stuck. Emit through the incident store (rule `_unpromoted-drift`
        or similar) so it dedups per content and lands in the one queue
        that remains. Sequence after the `blocks.d/` additions below —
        they merge spurious copies out of the very table this reads.
        **Blocked on the veto; the dependency is done (ec771f2) and the
        evidence now argues against the proposed predicate.** `seen>=2`
        fires on 7 copies today, every one of them historical — the newest
        span ends at 2.1.250.257 — while saying nothing about the two
        2.1.251 harness-fable copies that are what upstream is actually
        serving with no fixture. So it inverts the signal it was meant to
        carry: red on backlog, silent on news. Counter-proposal: fire when
        an uncovered core is carried at the newest cc_version on disk.
        That is 2 rows today (both 2.1.251 fable, already the subject of
        the concurrent-copies ruling below), it goes quiet the moment they
        are promoted, and it matches what the duty is actually for —
        patches keeping up with what is served now, not with 2.1.212.
        Recurrence then belongs in the *message*, not the predicate.
        Reviewed 2026-08-29: the recurrence proposer concedes — the table
        was re-run and confirms it (all 7 `seen>=2` rows end <=2.1.250;
        both 2.1.251 rows are `seen=1`). Recurrence measures how long a
        copy survived the backlog, not whether it is current, and the
        original nag objection mostly dissolves anyway once emission is
        incident-store dedup rather than a permanently-red check. One
        awaiting-veto predicate now: uncovered core at the newest
        cc_version on disk.
  - [ ] Docs last: rewrite CLAUDE.md "Standing maintenance" down to the
        single queue-triage duty; fold the event-driven checks into the
        hook's own description; `compress_traffic` bullet already needs no
        change (self-scheduling, failures already file incidents — a log
        tail was never a duty).
- [ ] <https:../proxy-memory-leak-2026-08-18/todo.kb/2026-08-18-000-confirm-store-retention-and-adopt-a-bound.md>
      (outside `.claude/`, so this breadcrumb is its only sweep visibility):
      restart done, fix-verification RSS capture done 2026-08-21 (99 MiB →
      141 MiB / ~66.6 h, ~30x slower than the pre-fix leak) — only the
      standing-RSS-monitoring ruling is left, open question for the user.
- [x] Add `blocks.d/` rules for the two session-optional blocks nothing
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
      of today's 22 uncovered copies should merge. Landed as three rules,
      not two: the auto-mode block has two wordings (v2.1.227 reworded its
      last paragraph from em-dashes to a parenthetical), so it is whole
      forms per `blocks.d/README.md` -- few alternatives, parts not
      independently optional. 22 -> 19 uncovered copies. Floors did not move
      at all, which is the general rule and worth remembering: a floor is
      what the *patch set* strips from a core, so deleting more core only
      moves it when a patch was matching inside the deleted text.
- [ ] Add a `blocks.d/` rule for the fork-provenance paragraph ("This
      conversation was forked out of {path}..."), the third uncovered
      session-optional block. Found the same way as the two above, while
      diffing v2.1.212.f03 harness-fable cores: with auto-mode and
      model-identity stripped, it is the remaining unexplained difference
      between two captures of one copy. Needs a `$` hole for the path (no
      mask tokenizes it today), so check whether a `masks.d/` rule for the
      path is the better half of the fix.
- [ ] Rule on how to promote two *concurrent* copies of one shape at one
      cc_version. `harness-fable` at 2.1.251 has two (`ada19cdbceea` from
      2.1.251.d59, `cb735fcae57c` from 2.1.251.171 -- was `6ee2dac2d820`
      until ec771f2 moved that core) differing on a reworded
      `<system-reminder>` harness bullet -- genuine copy drift, so the
      `blocks.d/` fix above did not merge them, as predicted. `system-prompts.kb/CLAUDE.md`
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

- [x] Stash `cc_version` on `Incident` records. Landed as `ffea89a`, three
      commits before the plan above filed it -- same session as the toil
      evaluation that proposed it. Source is the billing header's
      `cc_version=`, not the `User-Agent`: both carry it, but the addon has
      already parsed the body the billing header rides in. Records carry
      `model` too, since tool-description wordings vary by model family and
      the `upstream.d/` filename names whichever axis moved. First-seen, not
      latest -- the write is idempotent, and that is what keeps a live proxy
      from rewriting the record every request.
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
