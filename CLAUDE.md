--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-kb)
git-caution: personal
---

# mitmproxy: Claude Code traffic patching

Reverse-proxy in front of `api.anthropic.com` that records and rewrites
Claude Code traffic. Entry point: `proxy.sh`. Patches the system prompt
(`syspatch.py`) and thinking-redaction beta (`thinkpatch.py`); captures
pristine prompt bodies (`syscapture.py`); dumps flows to JSONL
(`flow2jsonl.py`).

## Collections

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
