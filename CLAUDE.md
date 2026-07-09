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

- Check `patch-failures/` for new incidents; triage per
  `CLAUDE.kb/patch-failure-triage.md`.
- Run `gc_patch_failures.py` occasionally to prune `patch-failures/_archive/`
  entries past their retention window.
