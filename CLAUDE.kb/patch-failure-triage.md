# Patch-failure triage

`log/patch-failures/` (gitignored) captures system-prompt bodies where a patch
didn't apply cleanly. An incident is one body, content-addressed: the verbatim
body at `_bodies/{digest}.md`, and one record per `(rule, kind)` at
`{rule}/{digest}.json`. `digest` is `incidents.content_hash()` — the body with
its per-session environment (cwd, scratchpad path, git status) neutralized, so
the same prompt dedups to a single incident across sessions and proxy restarts.

The capture primitives (`content_hash`, `save_body`, `save_incident`, the
`Incident` record) live in `incidents.py`, not `syspatch.py` — they're generic
over what's being captured. `syspatch.py`'s `report_issues` is the
patch-domain-specific caller (a body plus a list of match/search issues);
`incidents.capture_uncaught` is the other caller, used by all three addon
scripts (`syspatch.py`, `thinkpatch.py`, `flow2jsonl.py`) to wrap their
mitmproxy hooks: any exception that escapes the hook body is captured under
rule `_uncaught-{addon}` (kind = the exception's class name) via the same
content-addressed, idempotent-on-disk mechanism, then re-raised — capture,
not fail-soft. Same `_bodies`-style underscore-prefixed rule as
`_locate-system-prompt`, so it can't collide with a patch name.

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
  `content_hash` dedup still neutralizes session-volatile regions), non-text
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
  CLI shapes. Same reasoning also applies in `thinkpatch.py`: subagent
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
same cc_version, correlated with model: a long-form prompt (`# System`,
`# Doing tasks`, ...) on Sonnet-class models, and a short `# Harness`-style
prompt (`system-prompts.kb/v2.1.199-harness.md`) on Fable-class models.
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

Intent over letter: these patches exist to strip upstream bloat and resolve
contradictions with user instructions. When upstream removes the bloat, the
patch's job is done — sunset it, don't recreate it.

## After fixing

1. Capture the new body to `system-prompts.kb/v<version>.md` (see that
   collection's `CLAUDE.md`).
2. Run `check_patches` (defaults to the newest unsuffixed full capture; pass a
   variant capture explicitly to check the others) → expect zero warnings.
   Also run `check_dark_patches.py` — its per-patch match matrix shows
   patches gone silently dark on shapes they used to hit, which zero
   warnings cannot (match misses are silent by design).
   Older captures, and captures of a variant a patch doesn't target, are
   expected to warn — `matched-despite-upstream-removed` for sunset patches
   whose text still predates removal, or `failed-to-match` for a patch whose
   `search.md` target simply didn't exist yet at that older version. Neither
   is a regression.
3. Archive resolved incidents rather than deleting them outright:
   `incidents.archive_incident(rule, digest, CAPTURE_DIR)` (digest is the
   `{digest}.json` stem) moves it into `log/patch-failures/_archive/`, taking
   the shared body along only once no other live incident still
   references it. This keeps a just-resolved incident inspectable for a
   while; `gc_patch_failures.py`, run periodically (not automatic),
   reclaims anything left archived past its retention window.
