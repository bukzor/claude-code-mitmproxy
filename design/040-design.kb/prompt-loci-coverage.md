---
why:
  - ../010-mission.kb/final-say-over-injected-behavior.md
---

# Prompt loci coverage

The behavior-shaping text spreads over six request surfaces (inventory
and discovery method: `../../CLAUDE.kb/system-prompt-loci.md`).
Coverage is deliberate, not aspirational:

- `system` — patched (`prompt_patches.py`).
- `tools[].description` — patched (`tool_patches.py`).
- `tools[].input_schema.*.description` — unpatched; low bloat so far.
- `<system-reminder>` envelopes in user messages — unpatched by policy:
  their bulk is the user's own CLAUDE.md/agents/skills content, already
  under user control.
- `messages[]` entries with `role: "system"` — patched
  (`message_patches.py`, walked by `addons/syspatch.py`). The policy
  that spares the envelopes above is what argues for patching this one:
  none of this text is the user's. It is Claude Code's own instruction,
  injected mid-conversation -- plan-mode transitions, and the auto-mode
  bash-first steer that tells the model to prefer `cat`/`sed`/heredocs
  over Read/Edit/Write. One hazard is peculiar to the surface: it is
  interleaved with the conversation's own tool results, so a rule can
  match a quoted copy of itself, and anchoring around that is the rule
  author's job (`~/.config/claude-mitmproxy/system-message.d/README.md`).
- Per-turn envelopes (`<command-*>`, hook output) — unpatched;
  transient.
- Subagent request system prompts (`system` blocks where
  `is_subagent_request` is true — Task-tool subagent calls) — coverage
  is agent-type-dependent (shape details and live-probe evidence:
  `../../CLAUDE.kb/subagent-request-shape.md`):
  - The default/general-purpose agent type resends the interactive body
    verbatim, so it's already patched and captured today via the
    ordinary `locate_prompt_bodies` match — no gap,
    `is_subagent_request` never enters into it.
  - Specialized agent types (confirmed: `Explore`) send a genuinely
    distinct, agent-type-specific prompt that never carries
    BODY_MARKER. `prompt_location.locate_subagent_body` captures this shape
    (wired into `addons/syscapture.py`) — still unpatched, since there's not
    yet evidence on whether these prompts carry the same
    bloat/contradiction problems the interactive prompt does.

Extending coverage means a new walk, and usually the same template
patch machinery -- but not always: `tools[].description` earned its own
exact-compare semantics (`exact-compare-tool-stubs.md`).
