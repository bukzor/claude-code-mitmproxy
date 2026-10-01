# 2026-10-01 -- templates read as lines and matched as substrings

## What happened

Auditing `system-message.d/retune-auto-mode-bash-steer` turned up a mismatch
that every rule set sharing the patch dialect had: a template file reads as a
block of lines, but `template_to_regex` compiled it with no anchoring and
`first_hit` applied it with `re.search`, so it matched as a free-floating
substring. Three consequences were reproduced against real data. A quoted copy
of a rule is deleted while the live target survives, because `search` is
matched over the whole body independent of where `match` landed and takes the
leftmost hit -- and `misses == []`, so nothing is loud. An indented copy of the
envelope matches, since the heading never had to be at a line start. And
`fix-tone-conciseness` matched the text its own replacement had just written.

The README claimed the envelope anchor "is what excludes quoted copies". It
never did: the blank line after the heading broke numbered quotations as a
side effect of their prefixing, and styles that preserve blank lines (an
indented code block, unnumbered `cat` output) sailed through.

## What changed

`template_to_regex` wraps the pattern in zero-width line anchors, each omitted
when the template already carries its own `\n` on that edge. Zero-width because
`apply_masks` re-emits the template per hit: a consuming `(^|\n)` would eat the
newline from the masked output and break mask idempotence, the law
`check_laws.py` is the only detector for. The operator's ruling (2026-10-01):
anchor both edges, and the rule directories are ours to bring into line -- a
template that ends mid-line gets a placeholder.

Eleven config files moved. Measured over the 44 fixtures with `borrow_newline`
applied, every template's hit count is unchanged except
`fix-tone-conciseness/search.md`, 16 -> 15, and the lost hit is the rule's own
replacement output: a self-match bug fixed, not a regression to repair.
Two `replace.md` files changed in step with their templates, because a new
leading hole would otherwise delete what it covers -- an empty replacement
became `$PRE`. `strip-duplicate-parallel-tools/search.d/long-form.md` was
already at a line start, but took `$PRE` too: its sibling shares the one
`replace.md`, and a placeholder the search did not capture fails hard.

Two existing tests used bare fragments as templates (`MATCHES` inside a longer
line) and moved their bodies onto whole lines instead.

## Unratified calls

The three prose masks (`auto-memory-dir`, `memory-dir`,
`background-job-tmp-dir`) end mid-line in upstream prose. The brief's
recommendation, taken here and not ruled on, was to extend each verbatim to the
line end rather than add a trailing hole: a hole is masked, so it would hide a
reword from the digest, where a verbatim tail makes one break the mask and show
as churn. The brief did not know that `background-job-tmp-dir` has two
upstream tails on disk (v2.1.214 and v2.1.246), one a prefix of the other's
sentence, so verbatim means two files. It is now two.

`masks.d/cc-version.md` is `$PREcc_version=...` -- legible only once you know
the hole is `$PRE` and the literal starts at `cc_`.

## Out of scope, still open

An unnumbered verbatim quote of a steer arm sits at a genuine line start in
both copies, and leftmost still wins. Preferring a `search` hit inside the
`match` span would close it. Whether `message_patches` should treat replayed
tool results as ineligible was checked and is hard: replays and bulletins are
structurally identical, and composite messages carrying both occur.

## Disposed

`.claude/ideas.kb/2026-08-20-000-Audit-heading-anchored-match-md-templates-for-self-referential-collision-risk.md`
proposed grepping the `match.md` files for a bare heading with no leading
`\n` and hand-prepending anchors where a fixture confirmed it safe, or a
`check_laws.py` assertion so the gap could not recur. Anchoring by
construction answers both: there is nothing to audit and nothing to keep in
sync, and the one-off `\n` that `condense-delivering-work` carries still works
because a template that starts with `\n` is left alone. Deleted.
`2026-09-17-a-steer-that-arrived-where-nothing-patches.md` still cites it by
path; that narrative is what was true then.

## Follow-on: a file's trailing newline stops meaning anything

The operator ruled the same day that no file's trailing newline should be
load-bearing: strip one on read, append one on write, so strings in memory carry
no terminator and strings on disk always do. The case for it was already in the
corpus. `masks.d/` was split nine files to seven on whether they ended in a
newline, `tool-description.d/` fourteen to thirty-six, and each ending silently
changed what its file meant. It also rewrites the right-anchor branch the first
half had just added: with no template ever ending in its line break, that
branch is dead and the lookahead is unconditional.

`textfile.read`/`write` are the pair, and `tests/test_textfile_enforced.py`
asserts nothing else in the library calls `read_text`/`write_text`, with no
escape list -- a JSON or TOML parse is indifferent to the stripped newline, so
nothing needed one. `borrow_newline` and its four callers are gone.

The measurement harness did the work again. Before touching anything it saved
every fixture's patched, masked, core and digest output. First pass after the
change: 38 of 44 differed. Two causes, both a wrong guess of mine about what
"a deletion consumes one following newline" had to mean.

- At end-of-body there is no following newline, and the old code had been
  consuming the *preceding* one (it borrowed a newline for the deleted block,
  then stripped one from the end). A block at the very end of a body must
  strip to the same text as the body without it, or core digests split. The
  rule became `cut_lines`: the following break, else the preceding.
- A deletion is not "the replacement file is empty" but "the rewritten text is
  empty": `strip-duplicate-parallel-tools` replaces with `$PRE`, which is empty
  when the sentence is its own line.

Down to three, all `strip-git-status/match.d/v2.1.221.md` on a repo with no
commits. That variant alone had lost its terminator, so alone it never took the
line break its two siblings take; now it does, and the patched body for an
empty-commits session is one trailing newline shorter. Accepted as the
convention working, not a regression: the three older variants now agree.

Masks and every digest were identical on all 44 fixtures. The data migration --
one newline appended to the 44 fixtures and, because they are read the same
way, to the gitignored captures and incident bodies under `log/` -- lands with
the code. `survey-captures --current` reports no uncovered copies.

Not done, and noted by another session: the offline checks spend most of their
time in `check_laws.masks_that_split_a_class` (~23 of 31 seconds), which re-masks
all 240 bodies once per left-out mask. `(?m:^)`/`(?m:$)` in place of the
lookaround anchors measured 3x faster on a masking pass with identical output,
and a leave-one-out that only recomputes bodies the dropped mask touches is
exact. Neither is applied.

One slip in the commit that carried the convention, caught afterward by
touching `reload.py` and seeing no `lifecycle.reload` line follow: `reload.py`
is itself an addon, so importing `textfile` for its own reads put an unlisted
library module in front of its own `check_reloaded_covers_addon_imports`, and
it asserted on every re-execution -- a live proxy would have kept running the
old code, and a restart would have refused to start. Nothing ran the file, so
the suite stayed green. `tests/test_reload.py` now executes it in a
subprocess, and `textfile` is in `RELOADED`.
