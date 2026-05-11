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
