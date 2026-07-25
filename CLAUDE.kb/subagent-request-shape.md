# Subagent (Task-tool) request shape

A Task-tool subagent call is marked by `cc_is_subagent=true` in the
billing-header block (`system[0]`) -- but the *rest* of `system` varies
by agent type. This was confirmed by a live probe (spawning a real
subagent and inspecting its actual jsonl-capture entry), not by any
upstream documentation, since none exists.

Two shapes observed:

- **Default/general-purpose agent type** (the "claude" catch-all):
  resends the interactive body verbatim -- identical `system[1]`
  (`"You are Claude Code, Anthropic's official CLI for Claude."`) and
  `system[2]` (BODY_MARKER-prefixed) to a normal interactive session.
  Already patched and captured today via the ordinary
  `locate_prompt_bodies` match; `is_subagent_request` never enters into
  it.
- **Specialized agent types** (confirmed live: `Explore`): a different
  identity line at `system[1]` -- `"You are a Claude agent, built on
  Anthropic's Claude Agent SDK."` (this exact line is shared with the
  auxiliary CLI shapes in `syspatch.IDENTITY_LINES`) -- followed by an
  agent-type-specific prompt at `system[2]` (Explore's opens `"You are
  a file search specialist for Claude Code..."`). Never
  BODY_MARKER-prefixed. `syspatch.locate_subagent_body` walks this
  shape for capture; see
  `design/040-design.kb/prompt-loci-coverage.md` for the coverage
  decision this fed.

Only `Explore` has been directly observed live (two probes, 2026-07-13,
digests `d49649caa925` for the default-agent case and `0c1caf411ddb`
for Explore's specialized prompt). `Plan`, `claude-code-guide`,
`general-purpose`, `statusline-setup` are presumed to follow whichever
shape matches their nature but are unconfirmed -- worth checking each
against this doc's two shapes as evidence accumulates in
`log/prompt-captures/`, rather than re-deriving from scratch.
