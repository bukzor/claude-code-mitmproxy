---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [ ] Decide whether `driftwatch.sh` should run `--promote` itself. The
      framing this entry first had was wrong: it asked whether a background
      process should *write* fixtures unbidden, when writing is the step that
      can go wrong and committing is the step that catches it -- a commit
      touching `system-prompts.kb/` runs the whole offline suite, so
      `--promote` commits now and a red hook leaves the files in the tree with
      the check naming what it found. What is actually left to decide is
      whether the watch invokes it: that is one command's worth of toil per
      drift event, against a background process making commits on `main` with
      nobody reading first.

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
  - [x] Separate *logs* from *events*. Landed: `logging_handlers.py` (the
        `EventFileHandler` routing logger name to path, plus
        `reinstall_log_handlers`/`uninstall_log_handlers`), the `-s` addon that
        loads before everything else, `syscapture` emitting both capture events
        to their own loggers, and `reload.py` reinstalling after a module
        reload so both reload paths converge on one function while importing
        stays side-effect free. `tests/test_logging_handlers.py` (6, three
        mutations verified). Design:
        `design/040-design.kb/events-are-separate-from-logs.md`.
        Two findings worth keeping. The events logger must set its own level:
        inheriting leaves it at root's `WARNING` under a bare CLI, so every
        event silently vanished outside mitmproxy (which sets root to `DEBUG`).
        And pytest's `caplog` captures records by a route that survives
        `propagate = False`, so the first propagation test passed against a
        handler that had stopped reaching the root at all -- it uses a root
        handler of its own now.
  - [x] First consumer, and why this came up: `driftwatch.sh`. **The original
        arithmetic here was wrong and is corrected: the events file buys
        almost none of the claimed reduction.** Measured 2026-08-31: the
        predicate costs 1.03s, the 300s ceiling accounts for 288 of the ~290
        daily wakes, and real capture events run ~4/day (30-day sample of
        `log/prompt-captures/` mtimes, 2 files per new body). Because
        `save_prompt` writes only on a new masked digest, that directory is
        already content-addressed and *already* changes only on news -- so
        swapping it for an events file removes ~0.7% of the wakes. The lever
        is the ceiling, and it is independent of this task.
        What the swap does genuinely buy: a `masks.d/` edit makes
        `load_masked_digests` rewrite every stale masked sibling on the next
        request, up to ~150 `close_write` events in a burst, each costing a
        re-derivation for an input the predicate does not even read (it reads
        `blocks.d/`). Watching an events file drops that burst. Note also that
        only one of the three watches can ever be replaced: `system-prompts.kb/`
        and `blocks.d/` change when a fixture is promoted by hand, which is not
        a proxy event, and promoting is what clears a standing report.
        The shape that delivers ~10x: keep inotify on those two, swap
        `log/prompt-captures` for `log/events/capture`, raise
        `DRIFTWATCH_FLOOR` to 3600 (~30 wakes/day, ~31s CPU against ~5 min).
        The stronger version -- proxy evaluates the promotion
        predicate itself and logs only drift -- was weighed and set aside: it
        makes `system-prompts.kb/` a runtime input to the request path,
        reversing the direction `020-goals.kb/pristine-fixture-supply.md` and
        `offline-validation.md` establish.
        Landed as planned, plus two things the plan did not have. `modify` had
        to join the event set: the handler appends through an fd it holds for
        the proxy's lifetime, so a capture event's `close_write` arrives only
        when the proxy exits, and the swap as written would have been a watch
        that never fired -- the exact silent failure the ceiling exists to
        bound. And the loop `mkdir -p`s the watched directory, which the first
        event of its kind would otherwise create days later: inotifywait on a
        missing path fails, and this loop answers a failed watch by degrading
        to polling at the ceiling, which is now an hour. Verified live: an
        append through a held-open fd wakes it inside the ceiling (twice --
        the write, then the close), and the arming pass still prints once.
  - [ ] Keep the existing output conventions: gitignored under `log/`, append
        rather than truncate across restarts. Ruled 2026-08-31, against the
        earlier guess that one unsharded file would do: events are time-series
        output like `log/traffic/`, not content-addressed artifacts like
        `log/prompt-captures/`, and the date in the path is what makes a shard
        *finished* -- the unit compression, retention and `held_open()` all
        need. Naming is `log/events/<category…>/<type>.$DATE.log`, date as a
        leaf suffix so a type's whole history is one glob and `.log` stays the
        suffix `compress_traffic` reads. A stable `tail -F` target is a
        symlink beside it (verified: GNU tail 9.7 follows a symlink swap,
        reopening from the start, so no line is lost at midnight).
        Leaving mitmdump's own event log on stderr is a feature, not an
        oversight -- that stream is for watching a proxy interactively.
        Built except the symlink: shards, dates, append-across-restart and the
        gitignore are live, and `driftwatch.sh` consumes the directory rather
        than a stable filename, so nothing needs the `tail -F` target yet.
        Left unbuilt deliberately -- the constraint on its shape comes from the
        compression subtask below, which must not compress a symlink to the
        shard a proxy is holding open, so building it first would be building
        it blind.
  - [x] Reload-safe flocked fds, the primitive the handler needs.
        Landed: `flocked_logs.py` (`reopen_flocked_file`, `reopen_log_file`)
        plus `tests/test_flocked_logs.py` (7, both discriminating assertions
        mutation-verified). Design: `design/040-design.kb/ease-of-operation.kb/
        open-files-are-rediscovered-not-remembered.md` -- addon-reload and module-reload are
        exactly synonymous, so no `done()`/`DoneHook` and no module state; the
        fd is recovered by scanning `/proc/self/fd`, and flock's
        same-fd-idempotent / second-fd-conflicting pair makes a leaked reload
        distinguishable from a second proxy for free.
  - [x] The logger taxonomy, the published interface. **Ratified 2026-08-31**
        (agent-drafted, approved on no comment):
        `events.capture.{system-prompt,subagent-prompt}`,
        `events.incident.{patch-miss,strip-floor,uncaught}`,
        `events.lifecycle.{startup,reload}`,
        `events.housekeeping.{gc,compress}`. Four domains because each
        plausibly wants different handler config; segments are message
        categories, never emitting modules, so a refactor is not a breaking
        change. `log/compress_traffic.log` (3.6K, undated, the one existing
        append log with no date) folds into `housekeeping.compress`.
  - [x] Restart the proxy so `-s logging_handlers.py` takes effect. Done by the
        operator 2026-09-01T10:00:34; pid 19086 carries the load-first ordering
        and wrote its own `lifecycle.reload` line on the way up.
  - [ ] Rule on four defaults a session chose, none of them ratified
        (`Skill(review-open-questions)` batch, not loose ends -- the work
        around them is finished, so no sweep will surface them):
    - [x] **Ruled 2026-09-01** ("i don't love 1/2"): the events logger is
          `DEBUG`, not `INFO`. Setting a level at all is what keeps a durable
          record independent of console verbosity, but `INFO` added a second
          restriction nobody asked for -- it made a `debug`-grade event
          impossible, foreclosing the "perhaps with a debug-grade note" channel
          named for the rotator. `DEBUG` gates nothing here; `termlog_verbosity`
          decides what prints.
    - [x] **Ruled 2026-09-01** ("why direct to stderr? use the incident
          system?"): a failed write files an `_uncaught-events-log` incident.
          The stated default was also wrong -- `emit` had no `try`, so a
          `BlockingIOError` propagated out of the `logging.info()` call into
          the addon hook rather than reaching `handleError` at all. Now caught,
          filed, deduplicated, and guarded against re-entering this handler
          when `incidents` grows an `events.incident.*` record.
    - [ ] The 2 MB growth tripwire threshold, and `MIN_COMPRESS_BYTES = 1 MiB`.
          Both are round numbers over a measured ~13 KB/month, not derived.
    - [ ] The two testing rules added to `design/040-design.kb/` are marked
          agent-authored and vetoable in place; they are normative text a
          session wrote, not a ruling.
  - [ ] Wire the six taxonomy names that still have no emitter. `capture.*` and
        `lifecycle.reload` are live; `lifecycle.startup` (the three `load`-hook
        inventories in `syspatch`/`toolpatch`), `incident.{patch-miss,
        strip-floor,uncaught}` (beside the `logging.warning` in `incidents`,
        which stays -- the warning is the alarm, the event is the record) and
        `housekeeping.{gc,compress}` are still announcing to stderr only.
        Publishing a name and leaving it dead is the same defect this task
        exists to fix, one rung out.
  - [ ] Known edge, found by verifying against the live proxy: it holds the
        shard's flock for its lifetime, so a *second* process that emits an
        event is refused -- correct by design (one writer, loud on contention).
        Since the 2026-09-01 ruling that is no longer fatal to the emitter: the
        line is dropped and an `_uncaught-events-log` incident records why. But
        an offline tool whose events all vanish while the proxy runs is a bad
        deal either way. Today nothing outside `addons/` emits; decide whether
        offline tools should emit at all before that changes, and note the
        obvious alternative is a per-process shard suffix rather than one
        writer per file.
  - [ ] Growth tripwire, since the size estimate predates the system:
        ~13 KB/month predicted for `events.capture.*`, so alarm at 2 MB across
        `log/events/` (>100x). Occasion: proxy start, beside
        `gc_patch_failures.sweep_at_startup`; files an `_events-log-growth`
        incident rather than inventing a channel. Re-derive the threshold from
        measured rate once the taxonomy is populated.
  - [ ] Compression: wire `log/events` in, but give `compressible()` a minimum
        size so it self-noops (a 440-byte shard must not become a 300-byte
        `.zst`). One constant, and it correctly covers a tiny traffic shard
        too. Generalizing is `TRAFFIC_DIR`/`SUFFIXES` becoming parameters with
        a second call site under the existing lock -- not a second compressor.
- [ ] <https:../proxy-memory-leak-2026-08-18/todo.kb/2026-08-18-000-confirm-store-retention-and-adopt-a-bound.md>
      (outside `.claude/`, so this breadcrumb is its only sweep visibility):
      restart done, fix-verification RSS capture done 2026-08-21 (99 MiB →
      141 MiB / ~66.6 h, ~30x slower than the pre-fix leak) — only the
      standing-RSS-monitoring ruling is left, open question for the user.

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
