--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-kb)
depends:
    - Skill(llm-design-kb)
git-caution: personal
---

# mitmproxy: Claude Code traffic patching

Reverse-proxy in front of `api.anthropic.com` that records and rewrites
Claude Code traffic. Entry point: `proxy.sh`. Patches the system prompt
(`syspatch.py`) and thinking-redaction beta (`thinkpatch.py`); captures
pristine prompt bodies (`syscapture.py`); dumps flows to JSONL
(`flow2jsonl.py`).

Code and config both go live without a restart: mitmproxy re-executes an
edited `-s` addon on its own, and `touch reload.py` re-executes the shared
modules those addons import. That is why every local import in this repo is
`import x`, never `from x import y` -- `reload.py` asserts it, and
`CLAUDE.kb/reloading-a-live-proxy.md` explains why a from-import would
silently stop reloading.

## Generated output

Everything the proxy or its tooling writes at runtime is gitignored and
lives under `log/` -- never at repo root, never committed. Why unbounded
outputs are day-sharded and restarts append instead of truncate:
`design/040-design.kb/ease-of-operation.kb/`.

## Collections

- `design/` — layered why-chain (mission → goals → design) per
  `Skill(llm-design-kb)`; read before changing invariants (addon order,
  loudness, capture semantics).
- `CLAUDE.kb/` — deferred design/reference notes for this project (protocol
  shapes, gotchas) — read the relevant one before touching that area.
- `system-prompts.kb/` — captured system-prompt bodies per cc_version,
  used by `check_patches.py` for offline validation.
- `keying.claims.kb/` — the contestable commitments about what may key
  what, per `Skill(llm-claims-kb)`; entry point `keying.claims.md`. Read
  before changing how anything is named, deduped, or memoized. Where it
  overlaps `design/`, design.kb states the behavior and a claim says why
  that behavior is forced.
- `session.kb/` — dated incident/session narratives (what happened, why
  nothing was loud, what changed) — the durable record todo entries and
  commit messages point into.
- `.claude/todo.kb/` — strategic task breakdowns (per `Skill(llm-subtask)`).

Two in-repo rule sets share the patch template language, each with its own
`README.md`: `masks.d/` neutralizes session-volatile *content* for
`incidents.masked_hash` (validate with `check_masks.py`; an edit needs no
follow-up -- nothing stored is named by a masked digest), and `blocks.d/` deletes
session-optional *blocks* for `survey_captures.py`'s core-digest column only.
`check_laws.py` validates the algebra both rest on -- masking idempotent and
only ever coarsening, block deletions never overlapping.

## Standing maintenance

Always implicitly appended to the todo list (recurring, not a literal
checkbox to clear):

- Check `log/patch-failures/` for new incidents; triage per
  `CLAUDE.kb/patch-failure-triage.md`.
- Run `gc_patch_failures.py` occasionally to prune `log/patch-failures/_archive/`
  entries past their retention window.
- Run `compress_traffic.py` occasionally; `log/traffic/` is the only output here
  that grows without bound, and it compresses 13-57x because every turn resends
  the conversation prefix. Compressing is the answer instead of a retention
  window. It skips shards a running process still holds open, so the current day
  survives a run made while the proxy is up.
- Run `check_laws.py` after any `masks.d/` or `blocks.d/` edit; it is the
  only detector for a broken law, which otherwise yields a well-formed
  digest answering a different question than the one asked.
- Run `survey_captures.py` to spot captures whose *core* digest matches no
  promoted fixture; promote the fullest raw per shape (`cp` per
  `system-prompts.kb/CLAUDE.md`, then `check_patches.py`,
  `check_dark_patches.py`, `check_masks.py`). Promotion has no automatic
  trigger — additive drift is invisible to every loud mechanism until
  someone looks; the `_strip-rate` tripwire only catches
  subtractive/rewrite drift.
