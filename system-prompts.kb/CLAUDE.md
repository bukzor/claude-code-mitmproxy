--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-kb)
---

# Captured Claude Code System Prompts

Snapshots of the system prompt body Claude Code sends to the Messages API,
used as input to `check_patches.py` for offline patch validation.

## Naming

`v<MAJOR>.<MINOR>.<PATCH>.md` — full captured body for that cc_version.

`v<MAJOR>.<MINOR>.<PATCH>-<scope>.md` — partial capture covering only the
named section (e.g., `-doing-tasks` for `# Doing tasks` only). Patches whose
targets fall outside that section will report `failed to match` when run
against a partial; that's expected, not a regression.

`v<MAJOR>.<MINOR>.<PATCH>-<variant>.md` — full capture of a *concurrently*
served, structurally distinct prompt shape at that same cc_version (e.g.
`-harness` for the short `# Harness`-style prompt seen on Fable-class models,
vs. the unsuffixed long-form `# System`-style capture). Unlike a `-scope`
partial, this is a complete body — just not the "default" shape. No separate
registry to update: a patch scopes itself to a variant just by anchoring its
own `match.md` on a heading unique to that shape (see
`CLAUDE.kb/patch-failure-triage.md`). `check_patches` still defaults to the
newest *unsuffixed* full capture — pass a variant capture explicitly to
validate against it.

Likewise, patches sunset to `upstream-removed.bool` assert against the
*current* prompt: run against an old capture they report
`matched-despite-upstream-removed`, because the removed text is still present
there. Expected — which is why `check_patches` defaults to the newest capture.

## Adding a capture

Route Claude Code through `proxy.sh`, then extract the agent body from
`traffic.jsonl` via `jsonl2sysprompt.sh`:

```bash
./jsonl2sysprompt.sh traffic.jsonl > system-prompts.kb/v<version>.md
```

## What does not belong

- Patched outputs (regenerable via `check_patches.py`)
- Patch templates (those live in `~/.claude/system-prompt-patches.d/`)
- Non-system-prompt traffic (use `traffic.jsonl` raw)
