---
managed-by: Skill(llm-subtask)
status: todo
---

# Derive check provenance from declared inputs

**Priority:** medium -- no bug today; deletes two hand-maintained registries and
puts triage advice at the point of failure
**Complexity:** medium -- one declaration per check module (8), two or three new
predicates, one derivation; touches every `check_*.py` plus the hook config
**Context:** proposed 2026-10-01 while adding `check_inventory`. This file is
self-contained; no prior session context is needed.

> [!DRAFT] agent-authored 2026-10-01, vetoable. The operator asked for this to
> be filed as a standalone task and will rule on it in a later session. The
> design below is the agent's, including the rejected alternative; the one thing
> already ruled is that the distinction belongs in code rather than prose, which
> is why `monitoring/CLAUDE.md` now states a criterion instead of naming
> modules.

## Problem Statement

A red from `monitoring/` means one of two very different things, and which one
decides what the operator does next:

- `check_patches` can go red because upstream shipped new prompt text. Nothing
  in the repo changed. The answer is often to promote a fixture, and
  `--no-verify` on the commit is legitimate.
- `check_playbook` can only go red because someone edited the repo -- an event
  type added without a `playbook.kb/` entry. The answer is to fix that edit, and
  `--no-verify` suppresses a defect rather than deferring one.

That difference is currently recorded three separate times, in three
hand-maintained forms, none of which can tell when it has gone stale:

1. **The hook filter.** `.pre-commit-config.yaml` carries a `files:` regex
   naming the inputs a commit may touch. Hand-written, and a new check's inputs
   will not be in it.
2. **The skip policy.** `REQUIRES` in `monitoring/test_checks.py` names the
   checks whose data lives outside version control, so a checkout that has never
   run the proxy skips rather than fails. Hand-written, keyed per check.
3. **The triage reading.** `monitoring/CLAUDE.md` states which kind of red is
   which. Prose, consulted by a human mid-triage, if at all.

All three are projections of one fact: **what each check reads, and who writes
it.** Stating that fact once, in code, makes all three derivable and the
declaration itself enforceable.

## Current Situation

Eight checks, discovered by `check_verdict.all_checks()` rather than listed
(that part is done -- `check_inventory` holds the inventory in correspondence
with the `pyproject.toml` commands, and `monitoring/test_checks.py` asks for the
inventory instead of keeping one).

`REQUIRES` already draws half the line this task wants, which is the evidence
that the axis is the real one rather than one chosen for tidiness. The four
checks it names are exactly the four whose inputs are not version-controlled;
the four it omits are exactly the four whose inputs are:

| check                | reads                                           | in `REQUIRES` |
| -------------------- | ----------------------------------------------- | ------------- |
| `check_patches`      | `system-prompt.d/`, captured prompt bodies      | yes           |
| `check_dark_patches` | `system-prompt.d/`                              | yes           |
| `check_tool_patches` | `tool-description.d/`                           | yes           |
| `check_strip_floors` | `system-prompt.d/`, `log/prompt-captures/`      | yes           |
| `check_masks`        | `masks.d/`, `system-prompts.kb/`                | no            |
| `check_laws`         | `masks.d/`, `blocks.d/`, bodies on disk         | no            |
| `check_playbook`     | `playbook.kb/`, `logging_handlers.py`           | no            |
| `check_inventory`    | `check_*.py`, `pyproject.toml`                  | no            |

Note what that cut does *not* separate: `check_masks` and `check_laws` read
version-controlled inputs, yet `system-prompts.kb/` is written by automated
fixture promotion (`driftwatch.sh` runs the pass and commits it). So their red
can arrive without a human editing anything, which puts them on the triage side
despite their inputs being committed. One axis is not enough.

## Proposed Solution

Two axes per input, declared beside the check that reads it:

- **location** -- inside this repo, or outside it (`~/.config/claude-mitmproxy/*.d`, `log/`)
- **writer** -- a human editing, or a machine: upstream, the proxy, or an
  automated fixture promotion

Shape, in `check_verdict.py` next to `all_checks()` and `NOT_A_CHECK`:

```python
class Input(NamedTuple):
    path: Path
    writer: Writer  # HUMAN | PROMOTION | PROXY | UPSTREAM
```

and in each check module, beside its existing constants:

```python
INPUTS = (
    check_verdict.Input(incidents.MASKS_DIR, check_verdict.HUMAN),
    check_verdict.Input(prompt_patches.KB_DIR, check_verdict.PROMOTION),
)
```

Everything else derives:

- **hook filter** = inputs that are in-repo and `HUMAN`-written
- **`REQUIRES`** = inputs outside version control, which may legitimately be
  absent in a fresh checkout
- **triage kind** = every input `HUMAN` means red is a defect in this commit;
  any machine writer means red may be drift

### The declaration cannot be skipped

`check_inventory` gains the ratchet, in the form it already uses for the normal
form and the commands: a predicate reporting check modules that declare no
`INPUTS`. A new check without one fails the hook that a new check module already
fires.

### The hook filter stays written by hand, but cannot drift

`pre-commit` reads static YAML and cannot call Python, so the `files:` regex
remains literal. A `check_inventory` predicate closes the gap instead: every
in-repo `HUMAN` input must be matched by the committed regex. The regex stays
declarative; it just can no longer disagree with the declarations.

### The endpoint: no prose consulted during triage

`check_verdict.block()` already prints one line per predicate, on pass as well
as fail. With provenance declared it can print the kind too, so a failing check
carries its own reading -- "inputs are repo-local and human-written: this is a
defect in your commit" against "reads captured bodies: check whether upstream
moved." Nobody opens `monitoring/CLAUDE.md` mid-triage.

That is also the test of whether this was worth doing: the paragraph in
`monitoring/CLAUDE.md` should *shrink* to roughly one sentence -- a check
declares what it reads, and the verdict says which kind of red this is. If the
docs get longer, the arrangement is wrong.

## Implementation Steps

1. `Writer` and `Input` in `check_verdict.py`, beside `all_checks()`.
2. `INPUTS` in each of the eight check modules. Mechanical, but read each
   `collect()` rather than trusting the table above -- it was built from
   `REQUIRES` and module constants, not from the bodies of the collectors.
3. `check_inventory` predicates: `checks_without_declared_inputs`, and
   `hook_filter_missing_an_input` (in-repo `HUMAN` inputs the committed `files:`
   regex does not match).
4. Derive `REQUIRES` in `monitoring/test_checks.py` from the declarations and
   delete the hand-written table. Keep the skip behaviour identical: absent or
   empty directory skips, and the reason it skips rather than asserts stays in
   `monitoring/CLAUDE.md`.
5. Print the kind in `check_verdict.block()`.
6. Shrink the triage paragraph in `monitoring/CLAUDE.md` to the rule, deleting
   the criterion now stated there in prose.
7. Full suites, `pyright`, and one planted violation per new predicate -- plant
   a check module with no `INPUTS`, and an `INPUTS` entry the regex misses, and
   confirm the hook fails naming each.

## Rejected Alternative

**Split the two kinds into separate suites**, so each directory has a uniform
meaning of red. This is the obvious move and it is worse: it splits the
`check_*` normal form across two homes, breaks `monitoring/`'s "one command,
every property," and makes a check's kind a fact about which directory someone
filed it in -- the forgettable-registry failure in a new costume. One suite with
declared provenance beats two suites with implied provenance.

## Open Questions

- **How fine should `Writer` be?** Four values (`HUMAN`, `PROMOTION`, `PROXY`,
  `UPSTREAM`) are proposed, but only the human/machine split is load-bearing for
  the three derivations. `PROXY` and `UPSTREAM` may collapse. Prefer the coarsest
  vocabulary that still derives all three, and add a value when a derivation
  needs it rather than in anticipation.
- **Does `UPSTREAM` describe an input at all?** Upstream text arrives *inside*
  bodies the proxy captured, so the path's writer is the proxy and upstream is
  the content's author. Possibly a distinction without a difference here.
- **Should `binpatch` participate?** It reads the on-disk Claude Code binary,
  which is written by neither a human nor this proxy. It is not a check and has
  no predicates, so probably out of scope -- but it is the one reader whose input
  no axis above describes.

## Success Criteria

- Every check declares its inputs, and a check that does not fails the hook.
- `REQUIRES` no longer exists as a hand-maintained table; skip behaviour is
  unchanged.
- The `files:` regex cannot omit an in-repo human input without a red.
- A failing check prints which kind of red it is, without reference to a doc.
- The triage paragraph in `monitoring/CLAUDE.md` is shorter than it is now.

## Notes

**This presumes `check_inventory` has landed.** It was staged but not committed
when this file was written: `lib/claude_mitmproxy/check_inventory.py`,
`tests/test_check_inventory.py`, the `pyproject.toml` command, the discovery
function and `NOT_A_CHECK` in `check_verdict.py`, `CHECKS =
check_verdict.all_checks()` in `monitoring/test_checks.py`, the extended `files:`
regex, and the `monitoring/CLAUDE.md` revisions. Confirm those are in before
starting; the ratchet predicates attach to `check_inventory`.

**`claude-mitmproxy-check-inventory` needs a `uv sync` to exist as an
executable.** It was deliberately not run: a sync rebuilds `.venv` while the
live proxy runs out of it (`tests/CLAUDE.md`). `check_inventory` reads the
declaration in `pyproject.toml` rather than the installed scripts, so it is
accurate without one.

**Which half each piece belongs to.** `tests/` tests machinery against fixtures
it builds itself; `check_*.py` reads what is really on disk. The predicates here
are check-module code with their own seeded-fixture tests in
`tests/test_check_inventory.py`, which is the pattern
`tests/test_check_playbook.py` sets.

**Reload discipline.** Import modules, never their contents. `check_verdict` is
not addon-imported, so it is absent from `reload.py`'s `RELOADED`; if a check
module ever becomes addon-imported that changes, and `reload.py` asserts it.
