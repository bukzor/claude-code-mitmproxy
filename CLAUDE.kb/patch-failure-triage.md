# Patch-failure triage

`log/patch-failures/` (gitignored) captures system-prompt bodies where a patch
didn't apply cleanly. An incident is one body, content-addressed: the verbatim
body at `_bodies/{digest}.md`, and one record per `(rule, kind)` at
`{rule}/{digest}.json`. `digest` is `incidents.masked_hash()` — the body with
its per-session environment (cwd, scratchpad path, git status) neutralized, so
the same prompt dedups to a single incident across sessions and proxy restarts.

Each record also names the `cc_version` and `model` it came from
(`incidents.Origin`, supplied by the addon off the request it is already
patching). Both are **first-seen, not latest**, exactly like `at`: the write is
skipped once the record exists, which is what stops a live proxy rewriting it
on every request. cc_version is masked *out* of the body on purpose -- one
drift should dedup across every build carrying it -- so the record is the only
place it survives. `_uncaught-*` records say `unknown`: the hook wrapper
catches before anything is parsed, and re-parsing inside the `except` could
raise over the exception being reported. Date those from the traceback and the
reflog instead (see live-edit transients below).

The capture primitives (`masked_hash`, `save_body`, `save_incident`, the
`Incident` record) live in `incidents.py`, not `prompt_patches.py` — they're
generic over what's being captured. `prompt_patches.py`'s `report_issues` call
is the patch-domain-specific caller (a body plus a list of match/search
issues); `incidents.capture_uncaught` is the other caller, used by all four
addons (`addons/syspatch.py`, `addons/toolpatch.py`, `addons/thinkpatch.py`,
`addons/flow2jsonl.py`) to wrap their
mitmproxy hooks: any exception that escapes the hook body is captured under
rule `_uncaught-{addon}` (kind = the exception's class name) via the same
content-addressed, idempotent-on-disk mechanism, then re-raised — capture,
not fail-soft. Same `_bodies`-style underscore-prefixed rule as
`_locate-system-prompt`, so it can't collide with a patch name.

One incident class needs no fix: **live-edit transients**, a short burst of
`_uncaught-*` incidents timestamped within seconds of each other, whose
cause is already gone from the working tree. All three variants below
produce them, and all are archive-and-move-on.

Data half: `_uncaught-syspatch` `AssertionError`s whose messages name a
patch directory in a half-created state ("missing match.md", "no *.md
files in match.d/", missing replace.md). The proxy loads patches
per-request from the live directory, so editing
`~/.claude/system-prompt-patches.d/` while traffic flows makes every
intermediate file state load-bearing for a moment; affected requests pass
through unpatched (mitmproxy contains addon exceptions). To avoid causing
them: build a new patch dir outside `system-prompt-patches.d/` and `mv` it
in whole -- `mv` within a filesystem is atomic, `mkdir`-then-write is not.

Environment half: `_uncaught-syspatch` `AssertionError: rules dir missing
(wrong $HOME?)` -- not a malformed patch subdirectory but the whole
`~/.claude/system-prompt-patches.d/` tree transiently absent, because
`~/.claude` is itself a git repo an operator edits live. A `git rebase`
there briefly checks out a commit that doesn't have the directory (e.g.
`checkout origin/main` before the pick), and a request lands in that
window. Confirm with `git -C ~/.claude reflog --date=iso`: a
`rebase (start)`/`rebase (abort)` (or any checkout) pair straddling the
incident's `at` timestamp dates the burst, same as the code half's
`git log -S{symbol}` check.

Code half: `_uncaught-{addon}` `NameError`/`AttributeError` naming a symbol
that no longer exists, from a mid-refactor save mitmproxy re-executed
(2026-08-10: three `NameError: _rolled_over` in `addons/flow2jsonl.py`, ten
seconds apart, at three different line numbers -- three successive saves of
one refactor). Confirm with `git log -S{symbol}`: a commit that removed it
dates the burst, and the tree is coherent now. No `mv` trick applies here
-- each save is a whole, syntactically valid file, incomplete only across
the refactor -- so the burst simply ends when the refactor lands. Check
what the hook had already done before it threw: these three had emitted
their JSONL entry and died on the compressor trigger afterward, so no
traffic went unrecorded.

## Tool-description drift (`tooldesc-*`)

A second patch domain shares this capture machinery: `tool_patches.py` swaps
built-in tool descriptions for slim stubs, comparing the live text against
the accepted wordings in
`~/.claude/tool-description-patches.d/{Tool}/upstream.d/`. A mismatch still
gets the stub -- it's self-contained -- but captures kind
`changed-upstream` under rule `tooldesc-{Tool}`. Triage: diff
`_bodies/{digest}.md` against the accepted wordings, fold anything worth
keeping into `description.md` (or the `must-read.kb` entry it defers to),
then add the captured body as a new `upstream.d/*.md` named for the axis
that varies (model family, cc_version) -- wordings vary concurrently, so
accumulate rather than replace. The record's own `cc_version`/`model` are
what name that file; nothing else in the capture carries them, since a tool
description has no billing header to read them off. Verify with
`.venv/bin/claude-mitmproxy-check-tool-patches`
(expect zero warnings), then archive. Format and rationale: that
directory's `README.md`.

## The match/search model

Each patch has `match` (`match.md`, or `match.d/*.md` for ordered
alternatives, first hit wins) and optionally `search` (`search.md` or
`search.d/*.md`, same shape). They answer different questions:

- `match` — **is this patch applicable to this body at all?** A miss is
  always silent: wrong prompt variant, a session-optional block that's
  absent this time. No flag changes this.
- `search` — **the exact text to replace**, tried only after `match` hit.
  Defaults to whichever `match` template hit (so a plain single-`match.md`
  patch searches-and-replaces in one step). A miss is always loud
  (`failed-to-match`), and no flag can silence it: `match` proved the patch
  is in scope, so the precise target drifting away underneath it is a real
  regression.

`upstream-removed.bool` patches have no `replace.md` and no `search`;
`match` alone is the regression assertion — silent while the text stays
gone, loud if it reappears.

Two `kind`s, emitted by `apply_patches`:

- `failed-to-match` — `match` hit but `search` (or, absent that, `match`
  itself) didn't.
- `matched-despite-upstream-removed` — an `upstream-removed.bool` patch's
  `match` hit: Anthropic put back what we'd sunset.

One more, emitted by the addon's `request` hook before any patch runs, under
the non-patch rule `_locate-system-prompt/` (underscore-prefixed, like
`_bodies/`, so it can't collide with a patch name):

- `found-N-prompt-bodies` — a content-blocks `system` list didn't contain
  exactly one block starting with the prompt-body marker
  (`\nYou are an interactive agent`); the request passed through unpatched.
  The captured body is the whole list flattened: text blocks verbatim (so
  `masked_hash` dedup still neutralizes session-volatile regions), non-text
  blocks as JSON, with `=== system[i] ===` separators. Usual causes: the
  marker text drifted upstream, or a non-Claude-Code request shape.

  Known auxiliary CLI shapes (session-title generation, web-search helper)
  are exempt: `is_auxiliary_system` passes them through, no incident. It
  recognizes block *forms* (billing header, bare CLI identity line, an
  `AUX_TASK_PREFIXES` task opening, or an `AUX_TRAILER_PREFIXES` trailer
  such as the `## Session Context` block), so a drifted interactive prompt
  still captures.
  When a new auxiliary shape lands an incident, triage it the same way —
  if it's genuinely non-interactive, add its opening to `AUX_TASK_PREFIXES`
  (or, for a block that trails after the task prompt, `AUX_TRAILER_PREFIXES`)
  and delete the incident.

  Subagent requests (Task-tool invocations) are a second, separately
  recognized exemption: `is_subagent_request` checks the billing header for
  `cc_is_subagent=true` rather than enumerating block forms, because the
  actual prompt body is agent-type-specific (claude-code-guide, Explore,
  general-purpose, ...) — too open-ended to match block-by-block like the
  CLI shapes. Same reasoning also applies in `addons/thinkpatch.py`: subagent
  requests using classic (non-adaptive) reasoning send
  `thinking: {"type": "enabled", "budget_tokens": N}`, a config shape with
  no `display` field to set, so `_patch_thinking_body` treats it as a
  no-op alongside `"disabled"`.

  Both exemptions log at `logging.debug`, not `info` — every Task-tool
  call hits this path (this proxy sees traffic from every concurrent
  Claude Code session on the machine), so it fails the "happy to see this
  every time" bar for `info`. Compare the CLI-auxiliary case: low volume
  enough that its confirmation log was tolerable before it was unified
  with the subagent path onto the same `debug` line.

### The `_strip-rate` rule (aggregate tripwire)

Non-patch rule covering the one failure class per-patch loudness cannot:
an upstream rewrite that sends every shape-scoped patch silently out of
scope at once (the 2026-08-04 incident). After patching a main body,
`check_strip_floor` requires it to have stripped at least its shape's
floor -- half of what the current patch set strips from the *core* of the
newest promoted fixture of that shape, meaning that fixture with every
`blocks.d/` block deleted (`strip_floors`, computed live, no recorded
baseline to maintain). The core is what makes the floor safe: a fixture
carries whatever blocks its capturing session happened to have, and
half of a block-rich fixture can exceed what a sparse session strips at
all -- promoting v2.1.227-fable put the raw-derived floor at 1147 against
the 980 a git-less session strips. `check_strip_floors.py` is the
detector; run it whenever you promote a fixture or edit `blocks.d/`.
Two kinds:

- `unknown-shape-...` -- the body matches no `prompt_shape.py` marker: a new
  prompt shape. Capture it properly (it's already in
  `log/prompt-captures/`), promote a fixture, add patches, and add its
  heading to `SHAPE_MARKERS`.
- `low-strip-{shape}-{N}B-floor-{M}B` -- known shape, stripped less than
  half its fixture core's expectation: the shape drifted wholesale under
  a stable heading (promote + re-patch), or the fixture/patches moved and
  the floor is stale (floors cache per process --
  `touch lib/claude_mitmproxy/addons/reload.py`), or
  `blocks.d/` is missing a rule for a block the fixture carries, which
  leaves that block in the core and inflates the floor
  (`check_strip_floors.py` names it).

Triage ends with `archive_incident` like any other rule.

### The `_compress-traffic` rule (capture retention)

`compress_traffic.py` archives finished traffic shards and deletes the
originals, so it reports its own failures instead of leaving them to an
exit code: `addons/flow2jsonl.py` spawns one child per shard it opens -- usually
one per proxy lifetime -- so the parent that could read a returncode has
already exited by the time there is one to read. Kind is the exception
class, body is its traceback.

Nothing is lost when this fires. The capture is kept, its unverified
`.zst.part` is never published under the `.zst` name, and the sweep
continues past it -- but that capture sorts first on every later run, so
it keeps failing until fixed. Which shard and which stage is in
`log/compress_traffic.log`, the only place the child's stdout goes.

Usual causes: no `zstd` on PATH, a full disk (the archive needs ~2% of the
capture beside it), an unreadable capture. `tests/test_compression.py`
re-runs the sweep offline against seeded captures, including this path.
Archive when fixed, like any other rule.

### Split `match`/`search`, or single-file?

- **Split (`search` narrower than `match`)** — use whenever a reliable
  broad anchor exists: `match` asserts "this body carries the
  section/variant that always has the target", and `search` is the specific
  wording riding on that assertion. Drift within the asserted scope is then
  loud instead of invisible. `strip-doing-tasks-bloat` is the template:
  `match.md` = the `# Doing tasks` heading, `search.d/` = known wordings of
  the section body.
- **Single-file (no `search`)** — for genuine per-session optionality with
  no broader signal to anchor on (Fast Mode toggled, extra `--add-dir`
  paths, a git repo present at all). Don't manufacture a broad anchor here;
  it would fire loudly on ordinary, expected absence.

Either way, silence is only trustworthy for a patch that's been verified
against a real capture — see the "Subsumed" bullet below for how a silent
patch stayed stale for months.

## Concurrent prompt variants

Anthropic serves structurally distinct prompt shapes concurrently at the
same cc_version, correlated with model — since v2.1.221, three of them:
the long-form (`# System`, `# Doing tasks`, ...) on sonnet-5, and two
distinct `# Harness` shapes (opus gets `# Delivering work`/`# Corrections`,
fable gets `# Communicating with the user`). `prompt_shape.py` is the shared
classifier; `system-prompts.kb/CLAUDE.md` records fixture naming.
There is no variant registry — a long-form-only patch just anchors its
`match.md` on a heading unique to that shape (e.g. `# Tone and style`,
`# Doing tasks`, or `# System` for content in the un-headed preamble), with
the literal target in `search.md`. Headings are far more stable across
cc_versions than the wording under them, so `match.md` rarely needs
updating even when `search.md` does.

## Deciding the fix

Read `_bodies/{digest}.md`, find where the target went, then:

- **Reworded or moved, still present** → re-target `search.md` (or bare
  `match.md` for a single-file patch). If the wording differs across
  versions, convert to `search.d/`/`match.d/` with one template per wording
  (filename marks where it appeared, e.g. `v2.1.76.md`); first match wins.
- **Removed, and the patch only deleted it** → sunset: set
  `upstream-removed.bool`, remove `replace.md` and `search.md`. The patch
  becomes a regression assertion — silent while the text stays gone, loud if
  it returns.
- **Removed, but the patch also injected positive content** → still prefer
  sunset when that content is now redundant (e.g. already in the user's
  CLAUDE.md) or moot. Re-anchor it into the new prompt only if it still earns
  its place; don't re-inject bloat the upstream prompt no longer carries.
- **Present in one concurrently-served variant but not another** → anchor
  `match.md` on a heading unique to the variant(s) it belongs to, precise
  target in `search.md` (see above).
- **Subsumed by another patch's coarser match** → retire it (delete the
  directory), don't re-target. `strip-over-engineering` targeted two bullets
  that `strip-doing-tasks-bloat`'s whole-section template already deleted
  first (alphabetical load order) in every capture on file — it had never
  independently fired since at least v2.1.76, and its silencing flag
  (`conditional.bool`, a since-removed mechanism) hid that for months.
  Before re-targeting a "reworded" miss, grep the *patched* output for the
  target's surviving neighbors, not just the target itself — an
  earlier-sorted sibling may already cover the span.
- **Not present at all — match fired on this project's own text** →
  a bare-heading `match.md` (e.g. `# Delivering work`) is a plain substring
  search, so it can hit inside this repo's own captured `gitStatus` (a commit
  *message* naming the heading, not the heading itself — this project's
  commit history literally mentions its own patch targets). The tell: the
  body has no trace of the section anywhere, in a shape that shouldn't carry
  it (2026-08-20, `condense-delivering-work` fired on a sonnet long-form and
  a pre-convergence fable body via commit `873f6da`'s message). Fix by
  anchoring the template to a leading `\n` so it only matches a heading that
  starts its own line — real headings are always preceded by a blank line;
  a commit-log mention never is. Don't blanket-apply this to every
  heading-anchored `match.md` pre-emptively; fix it where it's actually fired.

Intent over letter: these patches exist to strip upstream bloat and resolve
contradictions with user instructions. When upstream removes the bloat, the
patch's job is done — sunset it, don't recreate it.

## After fixing

1. Capture the new body to `system-prompts.kb/v<version>.md` (see that
   collection's `CLAUDE.md`).
2. Run `check_patches` (checks only the newest unsuffixed full capture;
   variant fixtures are covered by `check_dark_patches.py`'s matrix) →
   expect zero warnings.
   Also run `check_dark_patches.py` — its per-patch match matrix shows
   patches gone silently dark on shapes they used to hit, which zero
   warnings cannot (match misses are silent by design).
   Older captures, and captures of a variant a patch doesn't target, are
   expected to warn — `matched-despite-upstream-removed` for sunset patches
   whose text still predates removal, or `failed-to-match` for a patch whose
   `search.md` target simply didn't exist yet at that older version. Neither
   is a regression.
3. Archive resolved incidents rather than deleting them outright:
   `.venv/bin/python -c 'from claude_mitmproxy import incidents;
   incidents.archive_incident(RULE, DIGEST, incidents.CAPTURE_DIR)'` (digest
   is the `{digest}.json` stem; import the module, never
   `from claude_mitmproxy.incidents import ...`, per
   `reloading-a-live-proxy.md`; the venv's own python -- `uv run` re-syncs
   `.venv`, which the live proxy is running out of) moves it into
   `log/patch-failures/_archive/`, taking the shared body along only once
   no other live incident still references it. This keeps a just-resolved
   incident inspectable for a while; `gc_patch_failures.py`, run
   periodically (not automatic), reclaims anything left archived past its
   retention window.
