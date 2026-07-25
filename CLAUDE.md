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
- `.claude/todo.kb/` — strategic task breakdowns (per `Skill(llm-subtask)`).

## Standing maintenance

Always implicitly appended to the todo list (recurring, not a literal
checkbox to clear):

- Check `log/patch-failures/` for new incidents; triage per
  `CLAUDE.kb/patch-failure-triage.md`.
- Run `gc_patch_failures.py` occasionally to prune `log/patch-failures/_archive/`
  entries past their retention window.
- Check `log/prompt-captures/` for cc_versions newer than the newest full-body
  capture in `system-prompts.kb/`; promote per the pattern in git log (`cp`
  newest raw long-form + harness, `check_patches.py`, `check_dark_patches.py`).
  Promotion has no automatic trigger — additive drift is invisible to every
  loud mechanism until someone looks.
