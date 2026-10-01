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
