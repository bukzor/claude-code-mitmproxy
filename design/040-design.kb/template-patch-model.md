---
why:
  - ../020-goals.kb/earned-silence.md
  - ../020-goals.kb/offline-validation.md
---

# Template patch model

Patches are declarative directories of literal-text templates with
`$PLACEHOLDER` holes — not diffs, not hand-written regexes. Literal
text survives upstream reformatting better than line-anchored diffs,
stays readable as prose, and compiles to a regex only as an
implementation detail.

There are two hole types and no third: `$NAME` spans the rest of a line,
`$...LINES` spans a run of non-blank lines. Both stop at structure they
cannot consume — a line break, a blank line — so the literal on either
side of a hole is a delimiter that always exists. A hole that could cross
blank lines has no such bound and is not offered; `load_templates`
rejects the one that used to be
(`keying.claims.kb/this-proxy.kb/no-hole-may-cross-a-blank-line.md`).

Either type may match nothing, because emptiness is a value the region can
take — a clean status, a repo with no commits — and a hole that cannot
match it makes its whole template miss on a body that is not actually
different. Allowing `$...LINES` zero lines does not relax its bound: an
empty match still cannot cross a blank line. What it does require is that
every template carry literal non-whitespace somewhere, or it would match
the empty string at every position; `template_to_regex` asserts that.

A template matches whole lines: its first line starts at a line start and
its last runs to a line end, and a template whose edge falls mid-line says
so with a hole. Authored text reads as a block of lines, so the compiled
pattern must not float free as a substring -- it would match a quoted or
indented copy of its own target, and text its own replacement just wrote,
silently. Both edges are zero-width, because a mask rewrites a hit to its
template verbatim and a consuming anchor would eat a newline from the output.
The operator ruled the rule directories ours to bring into line rather than a
fixed constraint on the compiler (2026-10-01).

A file's trailing newline carries no meaning. Every rule, fixture and capture
is read with one trailing newline stripped and written with one appended
(`textfile.py`, the only way the library touches a text file --
`tests/test_textfile_enforced.py` holds it to that), so no template ends in
the break of its last line and that break belongs to the body. The
convention governs files, not wire text: a body keeps whatever newline
upstream sent, which the line-end anchor absorbs. A rule whose rewritten text
is empty deletes lines, and a deleted line takes one break with it -- the
following one, else at end-of-body the preceding one, so a block at the very
end of a body strips to the same core as the body without it. Ruled
2026-10-01; format specifics are in the dialect README.

The `match`/`search` split is what makes earned silence expressible:
`match` (is this patch applicable to this body at all?) anchors on
stable structure like section headings; `search` (the precise text to
replace) carries the exact wording. Drift *within* an asserted scope is
loud, while out-of-scope absence stays silent.

Template compilation lives in `rule_templates.py`, imported by every
consumer: `prompt_patches.py` for the prompt patches, `incidents.py` for the
capture-digest masks (`content-addressed-capture.md`), and
`survey_captures.py` for the block strippers (`fixture-lifecycle.md`).
Applying a rule set *returns* its unapplied rules rather than reporting
them, so the caller owns the loudness decision — which is what lets one
format serve a mechanism whose misses are loud and ones whose misses are
silent by construction.

Normative format specs: `~/.config/claude-mitmproxy/system-prompt.d/README.md`
and `~/.config/claude-mitmproxy/tool-description.d/README.md`; the in-repo rule
sets (`masks.d/`, `blocks.d/`) use the same format and document their
own deviations in their `README.md`.
