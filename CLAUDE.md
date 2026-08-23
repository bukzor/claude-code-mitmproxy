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
(`prompt_patches.py`) and thinking-redaction beta (`addons/thinkpatch.py`);
captures pristine prompt bodies (`prompt_capture.py`); dumps flows to JSONL
(`addons/flow2jsonl.py`).

All the Python is one package, `lib/claude_mitmproxy/`; the repo root holds
only the shell entry points and the rule/knowledge directories. Its
`addons/` subpackage holds exactly the modules `proxy.sh` `-s`-loads, and
they hold nothing but mitmproxy hooks: the work is in the library module
each delegates to, which imports without mitmproxy and is therefore what
the offline checks run. Nothing outside `addons/` may import an addon --
`reload.py` asserts it, `addons/__init__.py` says why.

Code and config both go live without a restart: mitmproxy re-executes
an edited `-s` addon on its own, and
`touch lib/claude_mitmproxy/addons/reload.py` re-executes the library
modules those addons import. That is why every local import in this repo
names a module -- `from claude_mitmproxy import prompt_patches`, never
`from claude_mitmproxy.prompt_patches import apply_patches`. `reload.py`
asserts it, and `CLAUDE.kb/reloading-a-live-proxy.md` explains why importing
the contents would silently stop reloading.

## Binary patches (`binpatch.py`)

The proxy rewrites what crosses the wire; `binpatch.py` rewrites what does not.
It substitutes equal-length bytes in the on-disk Claude Code binary to undo
behavior compiled into the CLI that has no setting, env var, or hook and never
reaches the proxy. It runs as a SessionStart hook and re-applies itself after
each auto-update -- `CLAUDE.kb/binpatch-and-its-session-hook.md`.

What belongs: an equal-length byte substitution against compiled-in behavior
unreachable in transit, expecting the bun binary's two embedded copies and
refusing any other count. What does NOT: anything the proxy can rewrite in
flight -- that is a `prompt_patches`/`tool_patches` entry, not a binary patch.

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
session-optional *blocks* to answer "what would a session that switched nothing
on have sent?" -- `survey_captures.py`'s core-digest column offline, and the
live `_strip-rate` floor (validate with `check_strip_floors.py`).
`check_laws.py` validates the algebra both rest on -- masking idempotent and
only ever coarsening, block deletions never overlapping.

## Standing maintenance

Always implicitly appended to the todo list (recurring, not a literal
checkbox to clear):

- Check `log/patch-failures/` for new incidents; triage per
  `CLAUDE.kb/patch-failure-triage.md`.
- Run `gc_patch_failures.py` occasionally to prune `log/patch-failures/_archive/`
  entries past their retention window.
- `compress_traffic.py` needs no scheduling: `addons/flow2jsonl.py` spawns it for every
  shard it opens, so every proxy start sweeps yesterday and earlier. It skips
  shards a process holds open or wrote today, so running it by hand at any time
  is safe too. Failures land as `_compress-traffic` incidents, with the detail
  in `log/compress_traffic.log`; `tests/test_compression.py` re-runs the whole
  sweep offline against seeded captures.
- Run `check_laws.py` after any `masks.d/` or `blocks.d/` edit; it is the
  only detector for a broken law, which otherwise yields a well-formed
  digest answering a different question than the one asked. A `blocks.d/`
  edit also moves every `_strip-rate` floor, so run `check_strip_floors.py`
  with it.
- Run `survey_captures.py` to spot captures whose *core* digest matches no
  promoted fixture; promote the fullest raw per shape (`cp` per
  `system-prompts.kb/CLAUDE.md`, then `check_patches.py`,
  `check_dark_patches.py`, `check_masks.py`, `check_strip_floors.py`).
  Promotion has no automatic
  trigger — additive drift is invisible to every loud mechanism until
  someone looks; the `_strip-rate` tripwire only catches
  subtractive/rewrite drift.
