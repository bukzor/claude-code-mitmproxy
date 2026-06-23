# Patch-failure triage

`patch-failures/` (gitignored) captures system-prompt bodies where a patch
didn't apply cleanly. An incident is one body, content-addressed: the verbatim
body at `_bodies/{digest}.md`, and one record per `(rule, kind)` at
`{rule}/{digest}.json`. `digest` is `syspatch.content_hash()` — the body with
its per-session environment (cwd, scratchpad path, git status) neutralized, so
the same prompt dedups to a single incident across sessions and proxy restarts.

Two `kind`s, emitted by `apply_patches`:

- `failed-to-match` — a required patch's `match` didn't find its target.
- `matched-despite-upstream-removed` — an `upstream-removed.bool` patch's text
  reappeared, i.e. a regression: Anthropic put back what we'd sunset.

A `conditional.bool` patch that misses is **silent** — no incident, no warning;
it's allowed to no-op. So a conditional patch can quietly stop doing its job
after a reword. `check_patches` is how you catch that: it prints the char
delta, and a shrunken delta means a conditional patch went dark.

## Why a patch fails

Almost always: a new cc_version reworded, restructured, or removed the text the
patch targeted. (The v2.1.186 rewrite of 2026-06-23 broke seven patches at
once.) The fix is not to force the old match — it's to decide what the upstream
change means for the patch's *intent*.

## Deciding the fix

Read `_bodies/{digest}.md`, find where the target went, then:

- **Reworded or moved, still present** → re-target. If the wording differs
  across versions, convert `match.md` to `match.d/` with one template per
  wording (filename marks where that wording appeared, e.g. `v2.1.76.md`);
  first match wins.
- **Removed, and the patch only deleted it** → sunset: set
  `upstream-removed.bool`, remove `replace.md`. The patch becomes a regression
  assertion — silent while the text stays gone, loud if it returns.
- **Removed, but the patch also injected positive content** → still prefer
  sunset when that content is now redundant (e.g. already in the user's
  CLAUDE.md) or moot. Re-anchor it into the new prompt only if it still earns
  its place; don't re-inject bloat the upstream prompt no longer carries.

Intent over letter: these patches exist to strip upstream bloat and resolve
contradictions with user instructions. When upstream removes the bloat, the
patch's job is done — sunset it, don't recreate it.

## After fixing

1. Capture the new body to `system-prompts.kb/v<version>.md` (see that
   collection's `CLAUDE.md`).
2. Run `check_patches` (defaults to the newest capture) → expect zero warnings.
   Older captures warn `matched-despite-upstream-removed` for sunset patches;
   that's expected, not a regression.
3. Resolved incidents under `patch-failures/` are safe to delete — the body is
   preserved in the kb capture.
