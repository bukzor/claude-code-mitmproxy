# Where "the system prompt" actually lives in the wire protocol

The user-visible "system prompt" — instructions, examples, and context
that shape Claude Code behavior — is **not confined to**
`request["system"]`. It is distributed across at least six distinct
protocol surfaces inside each `/v1/messages` request body.
`addons/syspatch.py` rewrites the first and the last; `addons/toolpatch.py`
rewrites `tools[].description`. Which block of `request["system"]` is the
prompt body is `prompt_location.py` -- this note is how that surface was
mapped.

## Surfaces

| Locus                                                                        | Kind     | Examples                                                                                                                   |
| ---------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `system` (string or content blocks)                                          | known    | Main upstream prompt body                                                                                                  |
| `tools[].description`                                                        | known    | Bash tool description carries both nested-HEREDOC examples (`git commit -m "$(cat <<'EOF' …)"` and the `gh pr create` one) |
| `tools[].input_schema.properties.*.description`                              | new      | Per-parameter guidance and usage notes                                                                                     |
| `messages[].content[].text` (role=user) inside `<system-reminder>` envelopes | new, big | CLAUDE.md content, available agents list, available skills list, ToolSearch deferred-tools list                            |
| `messages[].content[].text` (role=user) inside other envelopes               | per-turn | `<command-*>`, `<local-command-*>`, `<user-prompt-submit-hook>`, `<persisted-output>`, `<bash-*>`                          |
| `messages[]` entries with `role: "system"`                                   | new      | Plan-mode transitions, permission-mode notices, the auto-mode bash-first steer -- and quoted tool results alongside them   |

## How `<system-reminder>` envelopes work

These are not in `system`. They are injected into the **opening
text block of user-role messages**, wrapped in
`<system-reminder>…</system-reminder>`. Four distinct kinds observed in
`traffic.jsonl`:

1. `As you answer the user's questions, you can use the following
context:` — followed by `# claudeMd` and the agent's CLAUDE.md tree
   (global + project + nested per-directory).
2. `Available agent types for the Agent tool:` — the agent listing.
3. `The following skills are available for use with the Skill tool:` —
   the skill listing.
4. `The following deferred tools are now available via ToolSearch …` —
   ToolSearch deferred-tools listing.

Older turns do not retain historical reminders; only the most recent
state is in flight per request.

## How `role: "system"` messages work

Distinct from the reminders above in three ways that matter to a patcher.
They are whole `messages[]` entries, not envelopes inside a user turn, and
their `content` takes the same two shapes `system` does: a bare string, or a
list of text blocks. They are Claude Code's own instruction -- observed
carrying a plan-mode transition notice and the auto-mode bash-first steer
concatenated into one message, under a `While auto mode is active:` heading.
And unlike a `<system-reminder>`, they **persist in history**: one observed at
`messages[22]` of 57, still there many turns after the transition it
announced. A rewrite here therefore has to be deterministic or it re-forks the
cached prefix every turn; a stable one costs a single cache miss.

A second hazard: tool results are replayed inside `role: "system"` messages
too, line-numbered, so this locus carries verbatim copies of whatever the
session has read -- including the patch rules themselves (observed at
`messages[3]` of a post-compaction request, opening `Called the Read tool with
the following input:`). A rule anchored on a short heading matches its own
quotation and deletes evidence out from under the reader. Anchoring against
that is the rule author's problem, worked through in
`~/.config/claude-mitmproxy/system-message.d/README.md`.

## False positive: `<system-reminder>` literally in `system`

The substring `system-reminder` appears ~600× across the `system` field
in captured traffic — but only as upstream prose _mentioning_ the tag
(the "prompt injection" bullet describing how `<system-reminder>` tags
should be interpreted). Mention, not use.

## Implication for `prompt_patches.py`

A complete patcher requires four targets:

1. `request["system"]` — `prompt_patches.py`.
2. Each `request["tools"][i].description` — `tool_patches.py` (whole-description
   stub replacement with an `upstream.md` drift tripwire; see
   `~/.config/claude-mitmproxy/tool-description.d/README.md`).
   `input_schema.properties.*.description` remains unpatched.
3. Each `request["messages"][i].content[j].text` where role is `user` —
   walk `<system-reminder>` envelopes and patch their bodies. Unpatched by
   policy — their bulk is the user's own CLAUDE.md/agents/skills content
   (`design/040-design.kb/prompt-loci-coverage.md`).
4. Each `request["messages"][i]` where role is `system` —
   `message_patches.py`, walked by `addons/syspatch.py` rather than an addon
   of its own: same job, same `_uncaught-syspatch` rule, and one parse of the
   request body instead of two.

The patch-format machinery (`rule_templates.Rule`, `.apply_rules`,
`.template_to_regex`, and `prompt_patches.apply_patches` over them) is fully
reusable; only the **walk** differs per locus. `message_patches.py` is the
demonstration: a walk and a rules directory, reusing `apply_patches`
unchanged. `tool_patches.py` deliberately does not reuse it: per-tool whole
replacement plus drift detection wants an exact-compare, not templates.

## Method

Top-level surface confirmed by successive subtraction on the full
captured stream:

```bash
jq -c 'select(.phase=="request" and .data.path=="/v1/messages?beta=true") |
       .data.content |
       del(.system, .tools, .messages, .model, .max_tokens,
           .metadata, .stream, .context_management,
           .output_config, .thinking) |
       keys' traffic.jsonl | sort -u
# → []   (top-level fully accounted)
```

Per-level drill-downs (tools, messages, content-block types) repeat the
same `del(…) | keys` pattern. `<system-reminder>` envelopes surfaced
via `awk` block-scanning on user-role text content.
