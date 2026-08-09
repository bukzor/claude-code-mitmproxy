---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [ ] Restart the proxy at a quiet moment: syscapture's subagent-body
      routing (mitmproxy@5c48772) and the new `masks.d/` digests are
      committed but the running process predates both. Only syscapture
      waits on this -- syspatch/toolpatch edits are already live via
      mitmproxy hot-reload
  - [ ] Afterwards, `rekey_captures.py --apply` once, to clear the
        old-scheme duplicate captures the stale proxy minted meanwhile
- [x] <https:todo.kb/2026-08-09-000-Masks-as-template-rules--quotient-session-noise-from-capture-digests.md>
