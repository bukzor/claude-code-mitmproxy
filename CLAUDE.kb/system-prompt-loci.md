# Where "the system prompt" actually lives in the wire protocol

The user-visible "system prompt" — instructions, examples, and context
that shape Claude Code behavior — is **not confined to**
`request["system"]`. It is distributed across at least five distinct
protocol surfaces inside each `/v1/messages` request body. `syspatch.py`
currently rewrites only the first.

## Surfaces

| Locus                                                                                 | Kind     | Examples                                                                                                                  |
| ------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| `system` (string or content blocks)                                                   | known    | Main upstream prompt body                                                                                                 |
| `tools[].description`                                                                 | known    | Bash tool description carries both nested-HEREDOC examples (`git commit -m "$(cat <<'EOF' …)"` and the `gh pr create` one) |
| `tools[].input_schema.properties.*.description`                                       | new      | Per-parameter guidance and usage notes                                                                                    |
| `messages[].content[].text` (role=user) inside `<system-reminder>` envelopes          | new, big | CLAUDE.md content, available agents list, available skills list, ToolSearch deferred-tools list                           |
| `messages[].content[].text` (role=user) inside other envelopes                        | per-turn | `<command-*>`, `<local-command-*>`, `<user-prompt-submit-hook>`, `<persisted-output>`, `<bash-*>`                          |

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

## False positive: `<system-reminder>` literally in `system`

The substring `system-reminder` appears ~600× across the `system` field
in captured traffic — but only as upstream prose *mentioning* the tag
(the "prompt injection" bullet describing how `<system-reminder>` tags
should be interpreted). Mention, not use.

## Implication for `syspatch.py`

A complete patcher requires three targets:

1. `request["system"]` — current `syspatch.py` scope.
2. Each `request["tools"][i].description` (and optionally
   `input_schema.properties.*.description`).
3. Each `request["messages"][i].content[j].text` where role is `user` —
   walk `<system-reminder>` envelopes and patch their bodies.

The patch-format machinery (`Patch`, `apply_patches`,
`_template_to_regex`) is fully reusable; only the **walk** differs per
locus. Folding all three into one addon vs. parallel addons is a design
choice; ambiguity should be low because each locus has a distinct
structural signature.

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
