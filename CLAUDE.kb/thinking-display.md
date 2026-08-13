# Restoring summarized thinking on Opus 4.7+ (`addons/thinkpatch.py`)

Since Claude Code v2.1.69 / Opus 4.7, `thinking` blocks come back with empty
text and only an opaque `signature` — ctrl-o in the TUI shows nothing. This is
server-controlled default behavior, not a Claude Code bug. `addons/thinkpatch.py`
restores **summarized** thinking. Verified working in practice (ctrl-o renders
summaries).

## Two patches, both required

The mechanism lives in `addons/thinkpatch.py`'s docstring/code; what isn't obvious there:

- It took **both** stripping the `anthropic-beta: redact-thinking-2026-02-12`
  header **and** setting `thinking.display="summarized"`. Either alone is
  insufficient — Claude Code sends that beta unconditionally, which forces
  redaction on Opus 4.7+ regardless of `display`.

## Subtleties for future work

- **`display` is model-defaulted.** Opus 4.7+ defaults to `"omitted"`; Sonnet
  4.6 / Haiku 4.5 default to `"summarized"`. The patch is therefore a no-op on
  the latter — safe to apply unconditionally. Re-check the default when a new
  model ships.
- **Claude Code sometimes sends `"omitted"` explicitly** rather than leaving
  `display` absent (observed 2026-07-09, incident `5e515c031c8d`). The
  request-body patch treats an explicit `"omitted"` the same as an absent
  field — both fall through to being overwritten with `"summarized"`; only
  `"summarized"` itself is a no-op.
- **Multi-turn continuity is safe.** The `signature` blob is byte-identical
  across display modes, so flipping `display` does not break tool-use / signature
  round-trips.
- **Claude Code always sends `thinking.type == "adaptive"`** (the asserts in
  `addons/thinkpatch.py` encode this observation). If a future version omits the field
  entirely, the body patch won't fire — and *creating* a thinking config risks
  enabling thinking where it was intentionally off. Inspect captured
  `traffic.jsonl` before changing that assumption.
- **Full/verbatim CoT is unavailable.** Only a separately-generated *summary* is
  returned on Claude 4; full chain-of-thought requires an Anthropic sales
  arrangement (only Sonnet 3.7 returned it by default). Don't chase it.
- **The `signature` can't be read locally.** It's envelope-encrypted protobuf
  (~7.81 bits/byte entropy, statistically uniform) — no local decrypt.

## Why proxy-patching (rejected alternatives)

- Patching Claude Code's `cli.js` — rejected: couples to the CLI, breaks on
  upgrade.
- Downgrading to v2.1.68 — rejected: strands the user on a stale CLI.

The proxy approach is decoupled and survives CLI upgrades, reusing existing
addon infrastructure.

## Reference

- Extended thinking: https://docs.claude.com/en/docs/build-with-claude/extended-thinking
- anthropics/claude-code#31326 — empty thinking since v2.1.69 (closed: not planned)
