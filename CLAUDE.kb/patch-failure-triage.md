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
   Older captures, and captures of a variant a patch doesn't target, are
   expected to warn — `matched-despite-upstream-removed` for sunset patches
   whose text still predates removal, or `failed-to-match` for a patch whose
   `search.md` target simply didn't exist yet at that older version. Neither
   is a regression.
3. Resolved incidents under `patch-failures/` are safe to delete — the body is
   preserved in the kb capture.
