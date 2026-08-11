---
label: BOUNDED_HOLES
standing: user
authority: operator ruling -- reject patterns without both a left-hand and a
    right-hand delimiter
why:
    - ../obligation.kb/observability-ranks.md
    - ../obligation.kb/prefer-dissolving-to-checking.md
---

# No Template Hole May Cross a Blank Line

Every placeholder the template dialect offers is bounded by structure it
cannot consume: the default `[^\n]*` by the line break, `$LINES` by the
blank line. Both bounds always exist, so the literal on either side of a
hole is a delimiter that is really there rather than one that is usually
there.

How many lines a hole may take is a separate question from what stops it,
and the answer is zero or more: an empty region is a value the region can
take, and an empty match still cannot cross the blank line. The one thing
the relaxation costs is that a template of nothing but holes now matches
the empty string -- every position in every body -- so `template_to_regex`
requires literal non-whitespace somewhere, which is the same demand as
"delimiters that are really there".

`$...BLOCK` was the exception, and the only one. It meant "the rest of this
top-level section" and approximated that as "up to the next `\n# `" -- a
right-hand delimiter that does not exist when the section is the body's
last, leaving a bare `.*`. Measured before removal: `scratchpad` ran to end
of body in 20 of its 51 occurrences and swallowed the following `gitStatus:`
paragraph in 15 of them.

No repair short of deletion works, because the bound is not expressible. A
greedy hole followed by a literal backtracks to that literal's *last*
occurrence, and the only literal that reliably starts a new section is
`\n# ` -- writing it into a block template hardcodes whichever section
happens to follow this one. Making the hole lazy and requiring a trailing
literal *does* bound it, and was rejected on other grounds: it preserves the
blind spot on copy rewritten inside a session-optional section, which is
upstream text the core digest exists to notice.

What makes deletion cheap rather than merely correct is an asymmetry in how
the two failures show up. Over-deletion is silent: two distinct bodies
collapse onto one core digest and the survey reports the second as already
seen. Under-deletion is loud: the block survives, the core digest moves, and
the survey shows a core matching no fixture, which is the row a human reads.
A literal template can only ever under-delete. That is `RANK`'s silent band
traded for its checked band, bought by removing a construct instead of
adding a check -- `DISSOLVE`, with the representation cost actually paid.

The cost is about 19KB of literal prose across six files, and any upstream
reword of a session-optional section drops its rule until someone
regenerates the template from a capture. That is the same cost model
`check_patches.py` already absorbs for every patch rule.

**What would kill it.** A session-optional region that is several paragraphs
long and has no stable literal anywhere in it -- content that varies every
session across blank lines. `$LINES` covers one paragraph of that and
nothing covers several, so such a region would have to go unstripped, or the
core digest would have to give up being byte-exact.
