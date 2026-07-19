---
managed-by: Skill(llm-subtask)
---
# Todo

- [x] Regular maintenance pass (2026-07-18)
  - [x] Triage `patch-failures/`: `tooldesc-Monitor` `changed-upstream`
    (Anthropic appended a PushNotification-usage paragraph to the
    `Monitor` tool description) — replaced
    `~/.claude/tool-description-patches.d/Monitor/upstream.md` with the
    new live text, folded the new guidance into
    `~/.claude/must-read.kb/before/using-claude-code-tool/Monitor.md`
    (new "Pushing notifications" section), `check_tool_patches.py` zero
    warnings, incident archived
  - [x] Triage `patch-failures/_locate-system-prompt/`: two
    `found-0-prompt-bodies` incidents, both genuinely auxiliary CLI
    shapes with drifted opening text — added
    `"Generate a short kebab-case name"` (session-title generation,
    reworded from `"Generate a concise, sentence-case title"`) and
    `"A user kicked off a Claude Code agent to do a coding task and
    walked away"` (new: the PushNotification phone-notification
    classifier) to `AUX_TASK_PREFIXES` in `syspatch.py`; verified both
    via `is_auxiliary_system`, incidents deleted (not archived — no
    patch content to keep, per `CLAUDE.kb/patch-failure-triage.md`)
  - [x] Promote newer `prompt-captures/` cc_versions into
    `system-prompts.kb/` (kb newest was v2.1.207/207-harness):
    `cp` newest long-form raw sonnet capture
    (`v2.1.214.ec3_claude-sonnet-5_645e76c13d04.raw.md` → `v2.1.214.md`;
    v2.1.208/212 long-form skipped, same "superseded before promoted"
    precedent as 202→207) and newest harness raw fable capture
    (`v2.1.212.f03_claude-fable-5_180f8505b0a0.raw.md` →
    `v2.1.212-harness.md`). `check_patches.py` zero warnings;
    `check_dark_patches.py` table unchanged (same 2 known-explained
    `v2.1.128`-only warnings, both new columns HIT/`-` match their
    v2.1.207/-harness predecessors exactly)
  - [x] Confirmed live: subagent-type prompt capture (the
    `locate_subagent_body`/`syscapture.py` work from the 2026-07-12
    session, deferred pending "next natural restart") — the running
    proxy has since restarted; `prompt-captures/` now has real
    subagent-body captures (`v2.1.214.67a`/`.31a`, both sonnet and
    opus-4-8, at least Explore/Plan-shaped bodies). Closes the open
    verification note in the 2026-07-12 entry below.
  - Not pursued this pass (flagging, not fixing): diffing
    `v2.1.207.md`→`v2.1.214.md` shows two new real (non-dynamic)
    long-form sections since the last bloat review closed —
    a they/them pronoun-default paragraph under `# Text output`, and a
    whole new `# Background Session` section (also present in the new
    `v2.1.212-harness.md`). Same shape as
    `ideas.kb/2026-07-08-000-*`; worth a similar pass if that's wanted.
- [x] Promote v2.1.207 captures into `system-prompts.kb/` (backlog found
  2026-07-12 review; kb newest is v2.1.202/203-harness)
  - [x] `cp` newest long-form raw capture
    (`prompt-captures/v2.1.207.a42_claude-sonnet-5_*.raw.md` →
    `v2.1.207.md`) and newest harness — a newer fable capture
    (`v2.1.207.c82_claude-fable-5_*.raw.md`, 2026-07-12) landed after the
    review that wrote this todo, so it (not `.468_`) went to
    `v2.1.207-harness.md`
  - [x] Run `check_patches.py` (both, zero warnings confirmed) and
    `check_dark_patches.py` (table clean, no unexpected MISS)
  - [x] Additive-drift bloat review done against v2.1.199 baseline: see
    `ideas.kb/2026-07-08-000-Review-v2-1-202-*` (resolved, no patches
    needed — original "new sections" premise was wrong, real drift was
    dynamic-content noise; see new
    `CLAUDE.kb/raw-capture-byte-diffs-include-dynamic-content.md`)
- [x] Add standing-maintenance bullet to root `CLAUDE.md`: check
  `prompt-captures/` for cc_versions newer than the newest kb capture
  (promotion currently has no trigger; additive drift is invisible to
  every loud mechanism)
- [x] `check_dark_patches.py`: flag subsumption — evaluate each `match`
  against text-as-patched-by-earlier-patches too; raw-HIT but
  patched-MISS = SUBSUMED. Found a live one on first run:
  `strip-help-feedback` anchored `match` on the same `# Doing tasks`
  heading `strip-doing-tasks-bloat` deletes wholesale, so it never fired
  on any current fixture — the `/help`+feedback bullets were shipping
  unstripped in every patched v2.1.207 request. Fixed in
  `~/.claude/system-prompt-patches.d/strip-help-feedback/` (match now
  targets its own text directly, search.md removed as redundant); not a
  repo change since patches live outside this git tree.
- [x] New finding from the above: `strip-colon-before-tools` and
  `strip-url-restriction` now show `failed-to-match` (match hit, search
  missed) on `v2.1.128.md` only — zero warnings on the current v2.1.207
  fixture, so not live-impacting, but worth understanding (real
  version-specific wording drift vs. an interaction with an earlier
  patch's edit) before deciding whether it needs a `search.d` split like
  `strip-doing-tasks-bloat` has.
  - Resolved: not drift, not subsumption (table shows plain `HIT`, not
    `SUBSUMED`). Both bullets are byte-identical in v2.1.76.md and
    v2.1.207.md but simply absent from v2.1.128.md's `# Tone and
    style`/`# System` sections — a content flicker on one archival
    snapshot. Exactly the documented-expected case in
    `CLAUDE.kb/patch-failure-triage.md`: "failed-to-match for a patch
    whose `search.md` target simply didn't exist yet at that older
    version. Neither is a regression." No `search.d` split needed —
    that mechanism is for multiple *currently valid* wordings, not a
    value that transiently didn't exist upstream.
- [x] `load_patches`/`load_tool_patches`: assert on malformed patch dirs
  instead of silently skipping (missing `match.*`/`description.md` is a
  config error, not out-of-scope — unearned silence)
  - Fixed: `load_patches` and `load_tool_patches` no longer pre-filter
    directories by required-file presence; they call `Patch.load`/
    `ToolPatch.load` unconditionally, letting the existing (and one new)
    assert fire loud. Added the missing `assert single.is_file() or
    multi.is_dir()` to `ToolPatch.load` for `upstream.md`/`upstream.d` —
    found via testing the fix, previously a bare `FileNotFoundError` from
    `multi.iterdir()`. `check_patches.py`/`check_tool_patches.py` zero
    warnings, `check_dark_patches.py` unchanged (2 known explained
    warnings).
- [x] Decide subagent-prompt coverage: `is_subagent_request` passes Task-tool
  prompts through unpatched *and uncaptured*, and no design doc records
  that as a decision — either add the by-policy sentence to
  `design/040-design.kb/prompt-loci-coverage.md` or treat as a new locus
  - Decided: agent-type-dependent, not a blanket gap. Initial grep-based
    check ("zero captures of subagent-marked content exist anywhere in
    prompt-captures/") was a flawed test — the billing-header marker
    structurally never appears inside a captured body regardless of
    coverage, so it proved nothing either way. Corrected via a live
    probe (spawned a real `Explore` subagent, inspected its actual wire
    request) plus a `traffic.jsonl` history scan: the default/
    general-purpose agent type resends the interactive body verbatim
    (already captured/patched today, no gap); specialized types
    (confirmed: `Explore`) send a genuinely distinct, never-BODY_MARKER
    prompt that's unpatched *and uncaptured*. Recorded precisely in
    `prompt-loci-coverage.md`'s new locus bullet + `[!TODO]`; also fixed
    `is_subagent_request`'s docstring in `syspatch.py`, which overclaimed
    "never carries BODY_MARKER" for all subagent requests.
- [x] Capture specialized-agent-type system prompts (content-hash keyed,
  like `syscapture.py` does for the interactive body) — new locus
  decided open in `design/040-design.kb/prompt-loci-coverage.md`;
  confirmed distinct for at least `Explore`, unknown how many distinct
  prompts exist across all built-in agent types
  - Implemented: `syspatch.locate_subagent_body` (joins every block
    after the billing header, for a bodyless subagent request); wired
    into `syscapture.py`'s capture loop. Validated the pure function
    directly against all 91 historical subagent requests in
    `traffic.jsonl` (89 general-purpose correctly return `None`, both
    known specialized-agent cases correctly extract the expected text)
    — strong evidence the logic is right.
  - NOT yet confirmed live: the running proxy (pid 1468, the one
    carrying this session) predates the edit and only re-reads
    `*-patches.d/` content per request, not Python module code (see
    `CLAUDE.kb/patches-reread-per-request.md` — same "ghost failure
    mode" class). A live probe post-edit produced no new capture file,
    consistent with stale bytecode, not a logic bug. Needs a proxy
    restart to take effect — deferred, since restarting it would
    interrupt the session currently using it. Confirm capture actually
    lands in `prompt-captures/` after the next natural restart.
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
