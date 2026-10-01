---
managed-by: Skill(llm-subtask)
status: in-progress
---

# Anchor patch templates to line boundaries

**Priority:** high -- closes a silent, actively misleading data-corruption bug
**Complexity:** medium -- one compiler change, seven config edits, measured harness already exists
**Context:** found 2026-10-01 while auditing
`~/.config/claude-mitmproxy/system-message.d/retune-auto-mode-bash-steer`. This
file is self-contained; no prior session context is needed.

## Problem Statement

`rule_templates.template_to_regex` compiles a template to a regex with no line
anchoring, and `first_hit` applies it with `re.search`. So every file in the
patch dialect *reads* as a block of lines but *matches* as a free-floating
substring. Authored intent and compiled pattern disagree, in all four rule sets
that share the dialect.

Three demonstrated consequences, each reproduced against real captured data:

1. **A quoted copy is deleted while the live target survives, silently.** Build
   one `role: "system"` message holding a line-numbered Read of
   `search.d/strict.md` followed by the live auto-mode envelope. `match` hits on
   the live envelope, legitimately. `search` is then matched over the whole body,
   independent of where `match` landed, and takes the *leftmost* hit, which sits
   inside the quotation. Result: the quoted copy is gutted, the live steer rides
   through unpatched, and `misses == []`, so nothing is loud. Three failures at
   once.
2. **An indented quotation matches.** A four-space-indented copy of the envelope
   matches, because the heading never had to be at a line start. Confirmed: the
   match begins at offset 14, preceded by spaces rather than a newline.
3. **A rule matches text it wrote itself.** `fix-tone-conciseness/replace.md`
   rewrites its target line into a two-line block whose second line is the same
   text indented three spaces. The unanchored search matches that output.

Why this locus makes it urgent: `role: "system"` messages carry replayed tool
results, 121 of 760 in one day's traffic, including verbatim copies of these very
rule files. A maintenance session reading the rules feeds them straight to the
matcher, so the collision concentrates exactly when someone is auditing.

## Current Situation

The only thing protecting us today is incidental. The live template demands a
*truly empty* line after its heading, so quoting styles that prefix every line
(numbered Read output, `>` blockquotes, diff markers) break the match as a side
effect of their prefixing. Styles that preserve blank lines (unnumbered `cat`
output, indented code blocks) sail through. Nothing in the rule asserts anything
about quotation.

The rule README currently claims the envelope anchor "is what excludes quoted
copies". That claim assumes `match` localizes the rewrite. It does not: `match`
answers "am I in scope?" and then `search` starts over from byte zero.

## Proposed Solution

In `template_to_regex`, wrap the compiled pattern in **zero-width** line anchors:

- prefix `(?:\A|(?<=\n))`, unless the template already starts with `\n`
- suffix `(?=\n|\Z)`, unless the template already ends with `\n`

> [!@bukzor] ruled 2026-10-01, recorded sensatim. Anchor both edges, not just
> the left. The rule directories are ours and are to be modified to conform to
> improved standards rather than treated as fixed constraints: "You seem to be
> missing the fact that these configurations are ours, are easily modified to
> conform with improved standards." Where a template ends mid-line because it
> uses a trailing literal as a delimiter, "Add a placeholder."

The anchors must be zero-width. A consuming form such as `(^|\n)` would eat the
preceding newline, and `apply_masks` re-emits the template text for each hit, so
the newline would vanish from the masked output. That breaks mask idempotence,
the law `check_laws.py` asserts, and the one whose violation yields a well-formed
digest answering a different question than the one asked.

> [!DRAFT] agent-authored 2026-10-01, vetoable. The invariant to record in the
> dialect README if this lands: *every template matches whole lines; a template
> whose edge falls mid-line must declare it with a placeholder.* This is
> self-documenting in a way the current files are not. Reading
> `` (`$JOBTMPDIR`) for any temporary files ... `` today tells you nothing about
> whether the author meant a line or a fragment.

### Config migration

Seven template files, plus two `replace.md` files that must re-emit a new
placeholder. Hit counts measured across all 44 fixtures in `system-prompts.kb/`
(excluding its `CLAUDE.md`), `borrow_newline` applied to each fixture:

| file | edit | hits now / anchored / rewritten |
| ---- | ---- | ------------------------------- |
| `masks.d/additional-working-dirs.md` | append `$PLATFORM` | 18 / 0 / 18 |
| `masks.d/cc-version.md` | prepend `$PRE` **and** append `$CCENTRYPOINT` | 1 / 0 / verify |
| `masks.d/auto-memory-dir.md` | close right edge (see open question 1) | 1 / 0 / 1 |
| `masks.d/background-job-tmp-dir.md` | prepend `$PRE`, close right edge | 2 / 0 / 2 |
| `masks.d/memory-dir.md` | close right edge | 1 / 0 / 1 |
| `masks.d/is-git-repo.md` | prepend `$INDENT` | 27 / 26 / 27 |
| `system-prompt.d/strip-additional-dirs/match.md` | append `$PLATFORM` | 18 / 0 / 18 |
| `system-prompt.d/strip-duplicate-parallel-tools/search.d/{harness,long-form}.md` | prepend `$PRE` | 43 / 16 / 43 |

`cc-version` is the one case a trailing hole alone does not fix: it is mid-line
on both ends. Appending `$CCENTRYPOINT` without also prepending `$PRE` leaves it
at 0.

Two replacements must change in step, or the new leading hole will delete text
it now covers:

- `strip-additional-dirs/replace.md` is currently ` - Platform:` and becomes
  ` - Platform:$PLATFORM`.
- `strip-duplicate-parallel-tools/replace.md` is currently empty (a deletion) and
  becomes `$PRE`.

`fix-tone-conciseness/search.md` needs **no** edit. It drops from 16 hits to 15,
and the lost hit is the rule's own replacement output. Anchoring fixes a
self-match bug there; restoring parity would be the wrong goal.

No other template moves. All 77 templates across `masks.d/`, `blocks.d/`,
`system-prompt.d/` and `system-message.d/` were measured; `tool-description.d/`
uses exact compare rather than templates and is unaffected.

## Implementation Steps

- [x] Write the two failing tests first, from the shapes in Problem Statement:
      a composite message (numbered quote of an arm, then the live envelope) and
      an indented copy of the envelope. The first must show the live steer
      deleted and the quotation intact; the second must show no rewrite.
- [x] Add the conditional zero-width anchors to `template_to_regex`.
- [x] Migrate the seven template files and the two `replace.md` files.
- [x] Re-run the parity measurement over the 44 fixtures. Expect parity
      everywhere except `fix-tone-conciseness` at 16 -> 15, which is intended.
- [x] Run the full suite and `monitoring/`, then pre-commit.
- [x] State the whole-line invariant in the dialect README
      (`~/.config/claude-mitmproxy/system-prompt.d/README.md`), and in
      `masks.d/README.md` wherever it describes template edges.
- [x] Correct the overclaim in
      `~/.config/claude-mitmproxy/system-message.d/retune-auto-mode-bash-steer/README.md`:
      the envelope anchor does not exclude quoted copies, because `search` is
      matched over the whole body independently of `match`.
- [x] Dispose of
      `.claude/ideas.kb/2026-08-20-000-Audit-heading-anchored-match-md-templates-for-self-referential-collision-risk.md`.
      It proposed grepping eighteen `match.md` files and hand-prepending anchors
      where a fixture confirmed it safe. Anchoring by construction answers it, so
      there is nothing left to audit or keep in sync. Record the reasoning on the
      way out.
- [x] Record the narrative in `session.kb/`.

## Open Questions

1. **Hole or verbatim extension, for the three prose masks**
   (`auto-memory-dir`, `background-job-tmp-dir`, `memory-dir`). `apply_masks`
   re-emits the template, so a trailing `$REST` masks whatever it absorbs. For
   `$PLATFORM` and `$CCENTRYPOINT` that is a feature: they are environment
   values, and masking them makes fixtures host-portable. For these three the
   tail is upstream prose, and a hole would hide genuine drift in it.
   Recommendation: extend verbatim to the line end for the three, accepting that
   an upstream reword breaks the mask, which is visible as digest churn.
2. Confirm that `fix-tone-conciseness` at 16 -> 15 is accepted rather than
   repaired.

**Resolved 2026-10-01** (agent, unratified; see
`session.kb/2026-10-01-templates-matched-as-substrings.md`): 1 -- verbatim
extension for the three prose masks, as recommended, except that
`background-job-tmp-dir` has two upstream tails on disk and so became two
files. 2 -- accepted, not repaired; the user has not confirmed.

## Success Criteria

- [x] Composite-message test: live steer deleted, quoted copy byte-identical.
- [x] Indented-quote test: no rewrite at all.
- [x] `fix-tone-conciseness` no longer matches its own replacement output.
- [x] 44-fixture parity as tabulated, with the single intended exception.
- [x] Full suite and `monitoring/` green; pre-commit green.

## Notes

**Two repositories.** `rule_templates.py`, `masks.d/`, `blocks.d/` and `tests/`
live in `~/claude/mitmproxy`. `system-prompt.d/` and `system-message.d/` live
under `~/.config/claude-mitmproxy/`, which is inside `~`, a separate git repo.
Both carry `git-caution: personal`. Commit only through `git commit-files` or
`git commit-staged` with explicit paths, and always `git -C <dir>`. Never
`git stash`. `~` is chronically dirty and shared with concurrent sessions, so
expect unrelated modifications and an occasional index lock.

**Reload discipline.** Import modules, never their contents. After editing a
library module, `touch lib/claude_mitmproxy/addons/reload.py` to re-execute it in
the live proxy; mitmproxy re-executes edited `-s` addons on its own.

**Measurement harness.** Compile each template with and without the anchors,
count `findall` hits across `system-prompts.kb/*.md` with `borrow_newline`
applied, and report every template whose count changes. Wrap the per-record work
in `try`/`except` and print the offending input on stdout, so one run yields the
debug information instead of costing a round trip.

**Out of scope, still open.** Two related items deliberately excluded:

- Preferring a `search` hit inside the `match` span, falling back to whole-body.
  Line anchoring closes the numbered-quote case but not an unnumbered verbatim
  quote, where the body sits at a genuine line start in both copies and leftmost
  still wins. That remains the backstop.
- Whether `message_patches` should treat replayed tool results as ineligible
  text. Checked and found hard: replays and bulletins are structurally
  identical, both arriving as a bare string or a text-block list with no
  distinguishing keys, and composite messages carrying both a replay and a live
  bulletin do occur, so a message-level exclusion would skip real targets.

## Follow-on: a uniform trailing-newline convention

Not started. Added 2026-10-01 at the operator's direction, to be done in this
same session: it rewrites the right-anchor branch this task just introduced, so
splitting the two means editing a compiler whose semantics changed underneath.

> [!@bukzor] ruled 2026-10-01, recorded sensatim:
>
> I believe all files should be treated identically whether they have a
> trailing newline or not. The trailing newline behavior is too unpredictable
> in too many software for it to be load-bearing.
>
> Proposal:
>
> - strip 1 trailing newline on read, if it exists.
> - append 1 trailing newline on write, unconditionally.
>
> This means strings in memory uniformly have no trailing newline (except where
> they are "additional blank lines" _content_), and strings on disk uniformly
> have a trailing newline (that's not "content").

Strip-one/append-one is a bijection, which is what makes this a convention
rather than a heuristic: a file ending in three newlines reads back as content
ending in two, and writing that content restores the file byte for byte.
`rstrip` would not have that property.

### Why it belongs in this task's session

`template_to_regex` chooses its right anchor with `template.endswith("\n")`.
Under the convention a template read from disk never ends in a newline, so that
test is always false, the branch is dead, and every template gets the zero-width
`(?=\n|\Z)` lookahead. The two changes are edits to the same four lines.

### The corpus today, which is the argument

145 template files across the four rule sets (`README.md` excluded):

| where                               | ends with `\n` | no trailing `\n` | empty |
| ----------------------------------- | -------------- | ---------------- | ----- |
| `system-prompt.d/`                  | 38             | 5                | 10    |
| `system-message.d/`                 | 3              | 0                | 1     |
| `masks.d/`                          | 9              | 7                | 0     |
| `blocks.d/`                         | 22             | 0                | 0     |
| `tool-description.d/` (exact compare) | 14           | 36               | 0     |

`masks.d/` is split 9 to 7 inside one directory, and `tool-description.d/` 14 to
36. Whether a given file ends in a newline is therefore already arbitrary, and
today it silently changes what the file means.

The files whose compiled behavior **changes** are the 72 that currently end in a
newline: they stop consuming it. The 12 that lack one are already in the
lookahead regime and are unaffected.

### What it deletes

`borrow_newline` and its four call sites (three in `rule_templates`, one in
`check_laws`). Its docstring states the problem being removed -- templates
ending in `\n` cannot match a block at end-of-body, so the body is lent a
newline and has it taken back. A zero-width right lookahead matches at
end-of-body natively, which is the whole job borrowing did.

Mask idempotence also stops being an argued property. The comment in
`template_to_regex` currently has to reason that a consuming `(^|\n)` would eat
a newline `apply_masks` re-emits from the template; with neither side carrying a
terminator, the rewrite is newline-neutral by construction.

### The companion decision: a deletion consumes one following newline

Today `search.d/strict.md` ends in a newline, so the match consumes `body\n` and
an empty `replace.md` removes the line together with its terminator. Strip that
newline and the match is `body` alone, so all 11 empty-`replace.md` rules would
start leaving a blank line where the content was.

So the convention needs a second half: when `replace` is empty, extend the
deletion span by one following `\n` when there is one. Well-defined, because
line anchoring now puts a template's right edge at a line boundary.
Replacements need nothing -- the stripped replacement drops into the span and
the body's own terminator survives, which is the wanted behavior.

This also makes the blank-but-not-empty `replace.md` hazard unrepresentable
rather than detected: a lone newline in `replace.md` reads back as the empty
string, so an end-of-file fixer can no longer quietly turn a deletion into a
blank-line insertion. The `Rule.load` assertion previously proposed for that is
then unnecessary.

### The exact-compare dialect is a separate question

`tool-description.d/upstream.d/*.md` is compared byte for byte against the wire
`description`, not compiled to a regex, and the wire text's trailing newline is
not ours to decide. Stripping on read means comparing stripped to stripped,
which is probably a bug fix rather than a behavior change: a stub that lost its
trailing newline to an editor currently fails to match an upstream description
that has one, and reports `changed-upstream`. Worth checking against the two
incidents presently queued under `tooldesc-Bash` before assuming they are drift.

### Migration, which is the bulk of the work

74 `read_text`/`write_text` sites across 15 library modules plus tests.

The data half is the risk. Under today's convention a file's bytes _are_ the
in-memory text; under the new one the file is the text plus a newline. So every
file whose logical content ends in a newline needs one appended, in the same
commit as the code. Otherwise `survey_captures` compares a stripped capture
digest against an unstripped fixture digest and reports drift on everything at
once. That is 44 committed fixtures in `system-prompts.kb/`, plus the gitignored
captures under `log/prompt-captures/`, which are regenerable but will produce
one pass of false drift if left behind.

### Enforcement

One helper pair, and a source-regex assertion that nothing calls the bare
`Path.read_text`/`write_text` outside it -- the form `reload.py` already uses
for its three invariants. It needs a documented escape list for the genuinely
non-text reads: `binpatch` reads bytes, `flocked_logs` reads `/proc/self/fd`,
and several modules parse JSON or TOML where a trailing newline is already
meaningless.

### Open Questions

1. **Where do the helpers live?** `repo_paths` is the only module everything
   already imports, and it is where `ROOT` lives, but it is currently three
   lines of path arithmetic with no behavior. The alternative is a new
   single-purpose module, at the cost of one more import everywhere.
2. **Does the convention govern wire text?** No, and it cannot: bodies arrive
   from the network with whatever trailing newline upstream sent. The
   convention is about files. The asymmetry is fine -- it is what the
   zero-width right anchor absorbs -- but it should be said out loud in the
   dialect README, because "strings in memory have no trailing newline" is only
   true of strings that came from disk.
3. **Does `masks.d/`'s 9-to-7 split hide existing bugs?** Seven masks currently
   do not consume their trailing newline and nine do. Check whether any of the
   nine depend on consuming it before converting, rather than assuming parity.

### Success Criteria

- [ ] `borrow_newline` is gone, with no caller left.
- [ ] All 44 fixtures produce byte-identical patched output before and after,
      using the measurement harness this task already built. This is the real
      safety property: the convention plus the deletion rule should reproduce
      current behavior exactly for the 72 newline-terminated templates.
- [ ] Any fixture that does differ is explained, not accepted by default.
- [ ] Nothing outside the helper pair calls `read_text`/`write_text`, asserted
      rather than documented, with the escape list carrying its reasons.
- [ ] The data migration lands in the same commit as the code, and
      `claude-mitmproxy-survey-captures --current` reports no new drift.
- [ ] Full suite and `monitoring/` green; pre-commit green.
