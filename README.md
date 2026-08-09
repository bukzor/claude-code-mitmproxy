---
last-updated: 2026-08-09
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

All generated output lives under `log/` (gitignored). Traffic is dumped to
`log/traffic/YYYY-MM-DD.flow` / `.jsonl`, sharded daily since a live proxy
can run for weeks without restarting.

## Addons

| Addon | What it does |
| --- | --- |
| `syscapture.py` | Records each unique system-prompt body — pristine, pre-patch (it loads before `syspatch.py`; addon hooks run in load order) — to gitignored `log/prompt-captures/`, as a content-addressed `.raw.md` / `.md` pair (verbatim / hash-masked, the latter a low-noise diff target). This is where new `system-prompts.kb/` captures come from (promote the `.raw.md`). |
| `syspatch.py` | Rewrites the system prompt using modular patch directories from `~/.claude/system-prompt-patches.d/` (format and rationale in that directory's README). A patch whose in-scope target has drifted warns loudly and captures the offending body under `log/patch-failures/` for triage — see `CLAUDE.kb/patch-failure-triage.md`. |
| `toolpatch.py` | Replaces built-in tool descriptions with slim stubs from `~/.claude/tool-description-patches.d/` (format in that directory's README). Upstream drift warns loudly and captures like a syspatch failure. |
| `thinkpatch.py` | Restores summarized thinking on Opus 4.7+: strips the `redact-thinking-*` beta header **and** sets `thinking.display=summarized` (both required — see `CLAUDE.kb/thinking-display.md`). |
| `flow2jsonl.py` | Streams every request/response as one JSONL line each. |

## Tooling

- `check_patches.py` — offline validation: applies the live patch set to a
  captured prompt body (default: newest full capture in `system-prompts.kb/`)
  and prints the patched result plus size stats to stderr. Expect zero
  warnings against the newest capture.
- `check_tool_patches.py` — same for tool-description patches, against each
  patch's own `upstream.md`.
- `check_dark_patches.py` — per-patch match matrix across all kb captures;
  run after promoting a new capture to spot patches gone silently dark
  (match misses are silent by design). `--pattern TEXT` instead asks which
  fixtures carry TEXT and whether the pipeline already strips it.
- `survey_captures.py` — inventory of `log/prompt-captures/`: shape,
  optional blocks, and promoted-yet per capture; the "someone looks" step
  of the standing promotion duty. Its `core` column is the digest with
  session-optional blocks stripped too, so an unseen core -- and only an
  unseen core -- means upstream shipped new prompt copy.
- `check_masks.py` -- offline validation of `masks.d/`: every mask is
  exercised by some fixture, masking is idempotent, and no two fixtures
  collapse to one digest. Mask misses are silent in production, so this is
  the only thing standing between a typo and every session minting a fresh
  digest.
- `rekey_captures.py` -- renames `log/prompt-captures/` entries to their
  digests under the current masks, trashing duplicates that collapse. Run
  after editing `masks.d/`, with the proxy restarted first.
- `flow2jsonl.sh` — replay a `.flow` file through the JSONL addon.
- `jsonl2sysprompt.sh` — extract the system-prompt body from a jsonl
  capture (`log/traffic/*.jsonl`). The live proxy records requests
  *post-patch*, which cuts both ways: bodies extracted here are
  contaminated as kb fixtures (those come from `log/prompt-captures/`,
  see `syscapture.py`) — but this is the only view of what a session
  *actually received*, since `log/patch-failures/_bodies/` stores
  pre-patch originals.

## Rule sets

Patches live in `~/.claude/` because they encode one operator's
preferences. Two rule sets live in-repo instead, sharing the patch
template language and its compiler (`templates.py`):

- `masks.d/` -- neutralizes session-volatile content (cwd, memory paths,
  model-id suffixes) before hashing, so a capture's digest is a property of
  the prompt rather than of the session that saw it.
- `blocks.d/` -- deletes whole session-optional sections, for
  `survey_captures.py`'s core-digest column only. Never part of the
  capture digest: whether a body carried `# Memory` is itself content.

## Knowledge bases

- `design/` — layered design docs (mission → goals → design): the why-chain
  behind the invariants, per its `CLAUDE.md`.
- `CLAUDE.kb/` — durable design notes and gotchas (where the system prompt
  actually lives in the wire protocol, patch-failure triage, thinking
  redaction); read the relevant note before touching that area.
- `system-prompts.kb/` — captured system-prompt bodies per Claude Code
  version, the fixtures `check_patches.py` validates against.

## License

Apache-2.0 (see `LICENSE`) — except the captured prompt bodies
(`system-prompts.kb/`), which are Anthropic's text reproduced for
interoperability and research; see `NOTICE`.
