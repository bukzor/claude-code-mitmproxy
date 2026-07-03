---
last-updated: 2026-07-03
---

# claude-code-mitmproxy

A mitmproxy reverse-proxy in front of `api.anthropic.com` that records and
rewrites Claude Code traffic in transit — patching the hardcoded system
prompt and un-redacting thinking summaries — without touching the CLI, so
it survives Claude Code upgrades.

## Quick start

```bash
./proxy.sh          # mitmproxy TUI, listening on :8080 (pass another port as $1)

# in another terminal:
ANTHROPIC_BASE_URL=http://localhost:8080 claude
```

All traffic is dumped to `traffic.flow` / `traffic.jsonl` (gitignored).

## Addons

| Addon | What it does |
| --- | --- |
| `syspatch.py` | Rewrites the system prompt using modular patch directories from `~/.claude/system-prompt-patches.d/` (format and rationale in that directory's README). A patch whose in-scope target has drifted warns loudly and captures the offending body under `patch-failures/` for triage — see `CLAUDE.kb/patch-failure-triage.md`. |
| `thinkpatch.py` | Restores summarized thinking on Opus 4.7+: strips the `redact-thinking-*` beta header **and** sets `thinking.display=summarized` (both required — see `CLAUDE.kb/thinking-display.md`). |
| `flow2jsonl.py` | Streams every request/response as one JSONL line each. |

## Tooling

- `check_patches.py` — offline validation: applies the live patch set to a
  captured prompt body (default: newest full capture in `system-prompts.kb/`)
  and prints the patched result plus size stats to stderr. Expect zero
  warnings against the newest capture.
- `flow2jsonl.sh` — replay a `.flow` file through the JSONL addon.
- `jsonl2sysprompt.sh` — extract the system-prompt body from a
  `traffic.jsonl` capture; this is how new `system-prompts.kb/` captures are
  made.

## Knowledge bases

- `CLAUDE.kb/` — durable design notes and gotchas (where the system prompt
  actually lives in the wire protocol, patch-failure triage, thinking
  redaction); read the relevant note before touching that area.
- `system-prompts.kb/` — captured system-prompt bodies per Claude Code
  version, the fixtures `check_patches.py` validates against.

## License

Apache-2.0 (see `LICENSE`) — except the captured prompt bodies
(`system-prompts.kb/`, `system.patched.md`), which are Anthropic's text
reproduced for interoperability and research; see `NOTICE`.
