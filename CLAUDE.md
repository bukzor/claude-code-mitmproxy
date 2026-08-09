--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-kb)
depends:
    - Skill(llm-design-kb)
git-caution: personal
---

# mitmproxy: Claude Code traffic patching

Reverse-proxy in front of `api.anthropic.com` that records and rewrites
Claude Code traffic. Entry point: `proxy.sh`. Patches the system prompt
(`syspatch.py`) and thinking-redaction beta (`thinkpatch.py`); captures
pristine prompt bodies (`syscapture.py`); dumps flows to JSONL
(`flow2jsonl.py`).

## Generated output

Everything the proxy or its tooling writes at runtime is gitignored and
lives under `log/` -- never at repo root, never committed. Why unbounded
outputs are day-sharded and restarts append instead of truncate:
`design/040-design.kb/ease-of-operation.kb/`.

## Collections

- `design/` — layered why-chain (mission → goals → design) per
  `Skill(llm-design-kb)`; read before changing invariants (addon order,
  loudness, capture semantics).
- `CLAUDE.kb/` — deferred design/reference notes for this project (protocol
  shapes, gotchas) — read the relevant one before touching that area.
- `system-prompts.kb/` — captured system-prompt bodies per cc_version,
  used by `check_patches.py` for offline validation.
- `session.kb/` — dated incident/session narratives (what happened, why
  nothing was loud, what changed) — the durable record todo entries and
  commit messages point into.
- `.claude/todo.kb/` — strategic task breakdowns (per `Skill(llm-subtask)`).

Two in-repo rule sets share the patch template language, each with its own
`README.md`: `masks.d/` neutralizes session-volatile *content* for
`incidents.content_hash` (validate with `check_masks.py`; after editing,
restart the proxy and run `rekey_captures.py`), and `blocks.d/` deletes
session-optional *blocks* for `survey_captures.py`'s core-digest column only.

## Standing maintenance

Always implicitly appended to the todo list (recurring, not a literal
checkbox to clear):

- Check `log/patch-failures/` for new incidents; triage per
  `CLAUDE.kb/patch-failure-triage.md`.
- Run `gc_patch_failures.py` occasionally to prune `log/patch-failures/_archive/`
  entries past their retention window.
- Run `survey_captures.py` to spot captures whose *core* digest matches no
  promoted fixture; promote the fullest raw per shape (`cp` per
  `system-prompts.kb/CLAUDE.md`, then `check_patches.py`,
  `check_dark_patches.py`, `check_masks.py`). Promotion has no automatic
  trigger — additive drift is invisible to every loud mechanism until
  someone looks; the `_strip-rate` tripwire only catches
  subtractive/rewrite drift.
