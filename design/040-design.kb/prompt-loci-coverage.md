---
why:
  - final-say-over-injected-behavior
---

# Prompt loci coverage

The behavior-shaping text spreads over five request surfaces (inventory
and discovery method: `../../CLAUDE.kb/system-prompt-loci.md`).
Coverage is deliberate, not aspirational:

- `system` — patched (`syspatch.py`).
- `tools[].description` — patched (`toolpatch.py`).
- `tools[].input_schema.*.description` — unpatched; low bloat so far.
- `<system-reminder>` envelopes in user messages — unpatched by policy:
  their bulk is the user's own CLAUDE.md/agents/skills content, already
  under user control.
- Per-turn envelopes (`<command-*>`, hook output) — unpatched;
  transient.
- Subagent request system prompts (`system` blocks where
  `is_subagent_request` is true — Task-tool subagent calls) — coverage is
  agent-type-dependent, confirmed by a live probe plus traffic history:
  - The default/general-purpose agent type resends the interactive body
    verbatim (byte-identical to a normal session's), so it's already
    patched and captured today via the ordinary `locate_prompt_bodies`
    match — no gap, `is_subagent_request` never enters into it.
  - Specialized agent types send a genuinely distinct, agent-type-specific
    prompt that never carries BODY_MARKER — confirmed live: an `Explore`
    call's request carried `"You are a Claude agent, built on
    Anthropic's Claude Agent SDK."` plus `"You are a file search
    specialist for Claude Code..."`, neither matched by
    `locate_prompt_bodies`. These are unpatched *and uncaptured*, not by
    policy — nothing walks this shape today, and `is_subagent_request`
    exists only to suppress the false-positive "no prompt body" incident
    this produces.

  > [!TODO]
  > Capture specialized-agent-type system prompts (content-hash keyed,
  > like `syscapture.py` does for the interactive body) before deciding
  > whether to patch them — confirmed distinct for at least `Explore`;
  > no evidence yet on how many distinct prompts exist across built-in
  > agent types, or whether they carry the same bloat/contradiction
  > problems the interactive prompt does.

Extending coverage means a new walk, and usually the same template
patch machinery -- but not always: `tools[].description` earned its own
exact-compare semantics (`exact-compare-tool-stubs.md`).
