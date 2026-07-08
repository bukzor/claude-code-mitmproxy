--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-design-kb)
---

# design/ — layered design documentation

Why-chain for this project: mission (010) motivates goals (020) motivates
design (040); entries link upward via `why:` frontmatter. Layer semantics
and the post-session maintenance pass: `Skill(llm-design-kb)`.

Belongs here: durable intent and invariants — the reasons the code is
shaped the way it is, especially the ones nothing else enforces.
Undecorated prose is descriptive of current behavior; `> [!TODO]` blocks
are normative.

Does not belong: operational gotchas and triage procedure (`CLAUDE.kb/`),
captured payloads (`system-prompts.kb/`), deferred ideas
(`.claude/ideas.kb/`), patch format specs (the `*-patches.d/` READMEs).

When to add: a session surfaces a goal or invariant future agents must
not accidentally violate. When to update: after architectural change,
run the skill's maintenance pass — if an entry contradicts the code, one
of them is stale.
