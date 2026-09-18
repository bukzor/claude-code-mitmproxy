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
- `playbook.kb/` — what addressing a watch line means: one entry per event
  type, named by the key the line starts with. `check_playbook` holds the
  two in correspondence; read an entry when its line arrives.
- `.claude/todo.kb/` — strategic task breakdowns (per `Skill(llm-subtask)`).

Two in-repo rule sets share the patch template language, each with its own
`README.md`: `masks.d/` neutralizes session-volatile _content_ for
`incidents.masked_hash` (an edit needs no follow-up -- nothing stored is named
by a masked digest), and `blocks.d/` deletes session-optional _blocks_ to
answer "what would a session that switched nothing on have sent?" --
`survey_captures.py`'s core-digest column offline, and the live `_strip-rate`
floor. `check_laws.py` validates the algebra both rest on -- masking idempotent
and only ever coarsening, block deletions never overlapping -- and is the only
detector for a broken law, which otherwise yields a well-formed digest
answering a different question than the one asked. Running it, and the rest of
the offline checks, is not a duty: the commit that edits either directory does
it (`.pre-commit-config.yaml`).

## Shorthand

- `routine maintenance` (or `regular maintenance`) -- open a maintenance
  session: see "Standing maintenance" below.

## Standing maintenance

> [!@bukzor] ruled 2026-09-01, recorded 2026-09-07, sensatim -- "Simply:
> address the Monitor output? If so, then adjusting responsibilities amounts
> to adjusting monitor output". Landed by 58e801c and cf671f1.

One duty: address the Monitor output. Arm `./driftwatch.sh` through
`Monitor` (persistent) when a maintenance session opens; it prints on its
first pass and then only when what it would print changes. Every line that
asks something starts with its event type, and `playbook.kb/<type>.md` says
what addressing it means -- so moving a responsibility onto or off the
operator is an edit to what the watch prints, and this instruction does not
change. A line with no key asks nothing (`committed N fixtures`, the
all-clear). A line starting `driftwatch:` is a tool that crashed, and its
output follows.

That there is only one duty is a design commitment, not an accident: every
other recurring obligation has been bound to the occasion that creates it or
argued away (`design/040-design.kb/every-duty-has-an-occasion.md`). The
watch is what binds the two that had no occasion -- fixture promotion, which
it runs and commits itself, and the patch-failure queue, which it reports as
a count per rule -- so a duty added here is a claim that neither was
possible.

Ask by hand with `claude-mitmproxy-survey-captures --current` (what the
watch checks); without `--current` for the backlog the watch deliberately
drops; with no argument for the full inventory, what is on disk rather than
what is missing; and `claude-mitmproxy-gc-patch-failures --queue` for the
queue.
