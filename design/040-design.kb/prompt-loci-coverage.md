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

Extending coverage means a new walk, and usually the same template
patch machinery -- but not always: `tools[].description` earned its own
exact-compare semantics (`exact-compare-tool-stubs.md`).
