---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [x] Collapse "Standing maintenance" to demand-driven: every polled duty
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
  - [x] Make `--drift` loud. Landed as `092e61a`: `Capture.release` (numeric
        triple, build tag dropped), `current_drift`, and the `--current` flag
        that applies the ratified predicate — 19 uncovered copies on disk, 2
        of them current. The channel changed on the operator's counter-
        proposal and is the better half of the design: not an incident record
        but `driftwatch.sh`, polled and arriving as a `Monitor` notification.
        Drift is a pure function of on-disk state, so a record of it would
        cache a derived value, and the incident queue is itself polled —
        routing drift there would have consolidated two polls, not retired
        one. First cut polled every 60s; corrected to an inotify wait over the
        predicate's three inputs, with a ceiling, after the operator installed
        inotify-tools: the "a capture event is a superset of a drift event"
        objection argues against *notifying* on the event, not against *waking*
        on it, and an evaluation measured ~1s of CPU, which polling pays for
        the life of the session. The sequencing
        constraint dissolved with the channel: a notification has no clearing
        semantics, so this no longer waits on the naming ruling. Bug caught
        by testing the failure path: merging stderr does not capture a shell's
        own "No such file" for an unexecutable check, so the first version
        went silent on exactly the failure it existed to report; it reads the
        exit status now.
  - [x] Docs last: rewrite CLAUDE.md "Standing maintenance" down to the
        single queue-triage duty; fold the event-driven checks into the
        hook's own description; `compress_traffic` bullet already needs no
        change (self-scheduling, failures already file incidents — a log
        tail was never a duty). Done except for the part that waits on the
        subtask above: the section is **two** duties, not one, because
        fixture promotion stayed polled until the drift predicate was built.
        Now closed: the section is one duty (triage), with arming
        `driftwatch.sh` named as session setup rather than as a second duty,
        and the by-hand commands kept as a trailing note. The
        `compress_traffic` bullet went earlier -- with gc now self-scheduling
        too, "these run themselves" is one clause pointing
        at the design entry rather than a paragraph per job, and the
        `_compress-traffic` detail was already in the triage kb.
        Also landed, which the plan did not anticipate: the theory itself.
        `design/020-goals.kb/earned-attention.md` (agent-inferred, marked
        vetoable) states it as the dual of `earned-silence` -- that goal
        binds the system's quiet, this one binds the operator's time, and
        both hang off the mission. `design/040-design.kb/`
        `every-duty-has-an-occasion.md` is the mechanism: the three routes
        (argue it away / bind it to its occasion / make it loud), which
        duty took which, and what makes an occasion usable. The drift
        predicate is a `[!QUESTION]` block there now, so the open decision
        lives in the tower rather than only in this file.
- [ ] Revamp the logging story across the addons. Every addon logs through
      `logging`, mitmdump sends the lot to stderr (`proxy.sh` does `exec >&2`),
      and nothing captures it -- `log/` holds only `compress_traffic.log`, from
      the compressor subprocess. So the proxy announces facts it knows exactly
      once and then discards the announcement. A `logging_handlers.py` addon is
      the likely shape: one place deciding where addon output lands, live-
      reloadable like everything else, and `-s`-loaded first so the other
      `load` hooks' startup inventories are captured too. It has precedent --
      `reload.py` and `quietconn.py` are both module-level config addons rather
      than hook carriers, and `quietconn` (capping `mitmproxy.proxy.server` at
      WARNING so connection chatter cannot bury real events) is already a
      fragment of this story that probably folds in.
  - [ ] Separate *logs* from *events*. `syscapture` logging "captured new
        system prompt -> path" is the exactly-once, deduplicated fact that a
        prompt copy was seen for the first time; a consumer wants that as a
        line in a tailable file, not as prose in a stream. Give those a logger
        name or handler of their own so nothing has to parse the mixed stream.
  - [ ] First consumer, and why this came up: `driftwatch.sh` waits on inotify
        across three directories with a 300s ceiling, so it wakes ~290 times a
        day and re-derives the whole answer (~1s) each time. Waiting on a
        capture-event line instead is ~5 wakes a day, on news rather than on
        file movement. The stronger version -- proxy evaluates the promotion
        predicate itself and logs only drift -- was weighed and set aside: it
        makes `system-prompts.kb/` a runtime input to the request path,
        reversing the direction `020-goals.kb/pristine-fixture-supply.md` and
        `offline-validation.md` establish.
  - [ ] Keep the existing output conventions: gitignored under `log/`, append
        rather than truncate across restarts, sharded by day if unbounded
        (`design/040-design.kb/ease-of-operation.kb/sharded-logs.md`). Capture
        events run a few lines a day, so one appended file is likely right.
        Leaving mitmdump's own event log on stderr is a feature, not an
        oversight -- that stream is for watching a proxy interactively.
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
- [x] Rule on how to promote two copies of one shape at one cc_version.
      **Ruled 2026-08-30: promote them all.** Both 2.1.251 fable copies are in
      as `v2.1.251-fable-61a97372.md` and `v2.1.251-fable-e7dd358b.md`;
      `--current` is quiet, backlog 19 -> 17, all five checks and 65 tests
      green. One correction while naming them: the suffix is the **raw**
      digest, not the core digest recommended below -- core digests move
      whenever `blocks.d/` changes (this very copy was `6ee2dac2d820` until
      ec771f2), and a name a rule edit can invalidate is what
      `content-addressed-capture.md` forbids. Detail below is the reasoning,
      kept because the policy rests on it.
      `harness-fable` at 2.1.251 has two (`ada19cdbceea` from 2.1.251.d59,
      `cb735fcae57c` from 2.1.251.171 -- was `6ee2dac2d820` until ec771f2
      moved that core). `system-prompts.kb/CLAUDE.md` names variants per
      *shape*, which has no slot for two copies of one shape at one version.
      Investigated 2026-08-30; the facts argue for picking one, and "concurrent"
      turns out to be the wrong word:
  - [ ] The whole difference is one `# Harness` bullet, reworded. Old
        (`.171`, seen Aug 28): "The system may send updates, reminders, or
        modifications to rules via mid-conversation system turns. These are
        system-controlled, unlike function results." New (`.d59`, seen Aug 29):
        "`<system-reminder>` tags in messages and tool results are injected by
        the harness, not the user." Cores are 37 lines each and differ on that
        line alone.
  - [ ] No patch anchors there, so the copies are patch-equivalent: nothing
        green against one goes red against the other. The only file under
        `~/.claude/system-prompt-patches.d/` mentioning the bullet is
        `strip-agent-prohibitions/README.md`, as prose about a different
        user-turn reminder; that patch's `match.md` is "Do not call the
        AgentTool $REST". Picking one therefore costs no coverage.
  - [ ] Not two simultaneous variants but the before and after of one
        rewording, both on disk because captures are permanent and sessions
        outlive a build. The build tag does not select the copy: `.d59` served
        harness-fable-new, harness-opus-old and long-form on the same day. The
        other three 2.1.251 shapes are already covered and consistent --
        `v2.1.251-harness.md` carries the new wording, `v2.1.251-opus.md` the
        old, and harness-opus has one core across `.c03` and `.d59`, so it has
        not flipped yet.
  - [ ] Superseded recommendation, kept because it is the fallback if the one
        below is rejected: promote `ada19cdbceea` as `v2.1.251-fable.md` and
        let the loser age out of `--current` when the release advances.
  - [ ] Better: promote *both*, because nothing needs a single winner. Of the
        four consumers, two want the group (`prompt_corpus.fixtures()` globs
        `*.md` for the dark-patch matrix; `survey_captures.promoted_cores()`
        is a set comprehension over every fixture), one cannot see variant
        fixtures at all (`prompt_corpus.latest_fixture()` matches
        `^v\d+\.\d+\.\d+\.md$`, so `check_patches`' target is unaffected by any
        suffixed file), and only `prompt_patches.strip_floors()` picks a
        per-shape winner -- which it already resolves itself, by
        `(version, len(text))`, without needing the filesystem to enforce
        uniqueness. Here it does not even bite: the copies differ by one bullet
        no patch matches, so both strip identically. The single-winner pressure
        came from the filename shape alone.
  - [ ] Naming, if both are promoted: `v<release>-<shape>-<core8>.md` once a
        slot holds more than one, applied to both so neither is privileged by
        promotion order. No route work -- `_fixture_version` is already suffix
        tolerant (`path.stem.removeprefix("v").split("-")[0]`), so the extra
        segment parses. Costs one `git mv` when the second copy arrives.
  - [ ] That also answers the flip-flop worry, which is narrower than it
        looks. `--current` is a pure function of disk state, so it cannot
        oscillate between checks; a copy can only re-enter when the release
        advances *and* a stalled rollout serves that body again under the new
        release -- at most once per copy per release. It only bites at all if
        declining to promote is a legal outcome, and today declining is forced
        by the one-name-per-slot limit. Remove that and promotion is always the
        answer, coverage is monotone, and the fixture doubles as the durable
        "seen and accounted for" record a mute would otherwise need. Consequence
        worth noting: promotion then becomes mechanical, which by this repo's
        own doctrine makes it a candidate for binding to its occasion rather
        than staying a notified duty.
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

- [ ] Consider injecting the attention signal into live session context, as a
      patch. Mostly superseded by `driftwatch.sh`, which covers the same ground
      far more cheaply; what is left is the one gap the design entry admits —
      the watch is only as live as the session that armed it, so drift that
      lands while no maintenance window is open waits for the next one. Prompt
      rewriting is the only push channel that does not need a window. Costs, if
      it is ever worth closing that gap: it rides every request until the
      condition clears (wants one-shot gating on the content-addressed dedup,
      not a standing paragraph), it reaches every subagent rather than the
      operator, and it moves the patched/original ratio `check_strip_floor`
      reads. It does *not* contaminate the drift measurement -- `syscapture`
      loads before `syspatch`, so captures stay pre-patch -- which was the
      objection worth checking first, and it comes back clean.
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
