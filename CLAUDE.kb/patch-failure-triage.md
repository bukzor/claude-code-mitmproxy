# Patch-failure triage

`patch-failures/` (gitignored) captures system-prompt bodies where a patch
didn't apply cleanly. An incident is one body, content-addressed: the verbatim
body at `_bodies/{digest}.md`, and one record per `(rule, kind)` at
`{rule}/{digest}.json`. `digest` is `syspatch.content_hash()` — the body with
its per-session environment (cwd, scratchpad path, git status) neutralized, so
the same prompt dedups to a single incident across sessions and proxy restarts.

## The match/search model

Each patch has `match` (`match.md`, or `match.d/*.md` for ordered
alternatives, first hit wins) and optionally `search` (`search.md` or
`search.d/*.md`, same alternatives-first-wins shape). They answer two
different questions:

- `match` — **is this patch applicable here at all?** A miss is always
  silent: no incident, no warning. Not matching just means this body doesn't
  have the thing this patch cares about — wrong prompt variant, a
  session-optional block that's absent this time, whatever. That's expected,
  not a failure.
- `search` — **the exact text to replace**, tried only after `match` already
  hit. Defaults to whichever `match` template hit when absent (so a plain
  single-`match.md` patch searches-and-replaces in one step, same as before
  this split existed). A miss here is **unconditionally loud**
  (`failed-to-match`) — there is no flag left that can silence it. `match`
  already proved this patch is in scope; `search` failing on top of that
  means the precise target drifted or vanished while the broader context
  held steady — a real regression to triage, not a shape difference to
  shrug off.

There is no longer a `conditional.bool` or `variants.txt`. A patch's own
`match` *is* its applicability check, full stop — match defines, unconditionally,
when search/replace is required to succeed.

`upstream_removed.bool` patches don't use `search` at all — they have no
`replace.md` and do no replacement; `match` alone is the regression assertion
(silent while the text stays gone, loud if it reappears).

### When to split `match`/`search` vs. leave it single-file

This is not "loud for real patches, silent for optional ones" — every
`match` miss is silent, full stop, no exceptions. The two shapes differ in
what a *miss* is allowed to mean, and that's set by whether `match` is doing
more than `search` would alone:

- **Single-file (`search` omitted, or textually equal to `match`)** — a miss
  is a plain, unremarkable "not applicable this time": genuine per-session
  optionality with no reliable broader signal to check against (Fast Mode
  toggled, extra `--add-dir` paths, a git repo present at all). There's
  nothing "softer" happening here versus a split patch — there's just no
  broader claim being made that a narrower miss could contradict.
- **Split (`search` narrower than `match`)** — `match` asserts something
  reliable and general ("we're on the variant/section that always carries
  this"), and `search` is the specific text riding on that assertion. Use
  this whenever such a reliable anchor exists, because it's strictly more
  informative: an unscoped miss stays silent, but drift *within* the
  asserted scope becomes loud instead of invisible. `strip-doing-tasks-bloat`
  is the template: `match.md` = `# Doing tasks` (always present when
  relevant), `search.d/` = known wordings of the section body (loud if none
  hit).

Don't manufacture a broad anchor just to make a patch "properly" split — if
doing so would make an ordinary, expected absence (most sessions have one
working directory) loudly fire on every occurrence, that's a sign there is no
real broader claim to assert, only day-to-day session variance. Single-file
is the correct, deliberate choice there, not a shortcut.

The failure mode to avoid is not "this patch is silent" — silence is the
designed behavior for both shapes on a `match` miss. It's **asserting a patch
is fine without checking it against a real capture**. `strip-over-engineering`
proved this: its `conditional.bool` silence was *itself* correct given its
match target, but nobody had verified in months whether that target was
still real vs. already subsumed by a sibling patch. Removing `conditional.bool`
doesn't remove the need to verify — it just removes the one place a stale
assumption used to be able to hide as a flag instead of a checked fact.

Two `kind`s, emitted by `apply_patches`:

- `failed-to-match` — `match` hit but `search` (or, absent that, `match`
  itself) didn't.
- `matched-despite-upstream-removed` — an `upstream-removed.bool` patch's
  `match` hit, i.e. a regression: Anthropic put back what we'd sunset.

## Concurrent prompt variants

Anthropic serves **structurally distinct prompt shapes concurrently**, at the
same cc_version, correlated with model rather than version: a long-form
prompt (`# System`, `# Doing tasks`, ...) seen on Sonnet-class models, and a
short `# Harness`-style prompt (`system-prompts.kb/v2.1.199-harness.md`) seen
on Fable-class models. There's no separate variant registry for this — a
patch whose target is long-form-only just gets a `match.md` anchored on a
heading unique to that shape (e.g. `# Tone and style`, `# Doing tasks`, or
`# System` for content in the un-headed preamble), with the precise literal
target moved to `search.md`. On the harness variant that heading is absent,
`match.md` misses, the patch is silently out of scope; on the long-form
variant `match.md` hits and `search.md` had better find its target too, or
that's a loud regression.

Section headings make good `match.md` anchors: they're far more stable across
cc_versions than the sentence-level wording underneath them, so they rarely
need updating even when the patch's own `search.md` does.

## Deciding the fix

Read `_bodies/{digest}.md`, find where the target went, then:

- **Reworded or moved, still present** → re-target `search.md` (or bare
  `match.md` for a single-file patch). If the wording differs across
  versions, convert to `match.d/`/multiple templates, one per wording
  (filename marks where it appeared, e.g. `v2.1.76.md`); first match wins.
- **Removed, and the patch only deleted it** → sunset: set
  `upstream-removed.bool`, remove `replace.md` and `search.md`. The patch
  becomes a regression assertion — silent while the text stays gone, loud if
  it returns.
- **Removed, but the patch also injected positive content** → still prefer
  sunset when that content is now redundant (e.g. already in the user's
  CLAUDE.md) or moot. Re-anchor it into the new prompt only if it still earns
  its place; don't re-inject bloat the upstream prompt no longer carries.
- **Present in one concurrently-served variant but not another** → give it a
  `match.md` anchored on a heading unique to the variant(s) it belongs to,
  with the precise target in `search.md` (see above).
- **Subsumed by another patch's coarser match** → retire it (delete the
  directory), don't re-target. `strip-over-engineering` targeted two bullets
  that `strip-doing-tasks-bloat`'s whole-section template already deletes
  first (alphabetical load order) in every capture on file — it had never
  independently fired since at least v2.1.76. `conditional.bool` (the old
  mechanism) hid this for months; the fix wasn't a new template, it was
  recognizing the patch was dead weight. Before re-targeting a "reworded"
  miss, check whether an earlier-sorted sibling patch's match already covers
  the same span in the *working* (patched) output — grep the patched text for
  the target's surviving neighbors, not just the target itself.

Intent over letter: these patches exist to strip upstream bloat and resolve
contradictions with user instructions. When upstream removes the bloat, the
patch's job is done — sunset it, don't recreate it.

## After fixing

1. Capture the new body to `system-prompts.kb/v<version>.md` (see that
   collection's `CLAUDE.md`).
2. Run `check_patches` (defaults to the newest unsuffixed full capture; pass a
   variant capture explicitly to check the others) → expect zero warnings.
   Older captures, and captures of a variant a patch doesn't target, are
   expected to warn — `matched-despite-upstream-removed` for sunset patches
   whose text still predates removal, or `failed-to-match` for a patch whose
   `search.md` target simply didn't exist yet at that older version. Neither
   is a regression.
3. Resolved incidents under `patch-failures/` are safe to delete — the body is
   preserved in the kb capture.

## Open verification items

- `strip-fast-mode-info`'s `match.md` targets a `<fast_mode_info>` tag reading
  "uses the same Claude Opus 4.6 model" — but the *unconditional* Fast Mode
  line elsewhere in the current prompt already says "Opus 4.8/4.7". That's
  the same kind of stale-version smell `strip-over-engineering` had. No
  capture on file has Fast Mode actually toggled on, so this is unverified,
  not confirmed broken — get a capture with `/fast` enabled and check the
  tag's current wording before trusting this patch.
