# Session-optional block rules

One file per block, `<what-it-is>.md`, holding a template in the same
language as the masks next door (`$PLACEHOLDER` holes in literal prose).
Every hit is **deleted**, and the block's name is reported as present.

Only `survey_captures.py` reads these. They produce its `core` column -- the
digest of a body with every block this session happened to switch on removed
-- so two captures share a core digest exactly when they carry the same prompt
copy, whatever their sessions differed on. The question that answers is "has
upstream shipped new prompt text?", which is the trigger for promoting a
fixture (`system-prompts.kb/CLAUDE.md`).

They are never part of `incidents.masked_hash`. Block *presence* is content:
a capture that carries `# Memory` is a different observation from one that
doesn't, and first-seen-wins dedup would throw the fuller one away.

## Blocks are stripped from the masked body

Masks run first, so a template here can be written against the tokens masks
leave behind rather than the volatile text they replaced -- `git-status.md` is
a dozen literal lines because `$GITBRANCH` and friends are already tokens by
the time it runs.

## Deletions never overlap, so order cannot matter

Every block is tried against the result of the previous ones, and no rule may
*depend* on an earlier rule having fired: the set is loaded in filename order,
which is alphabetical and carries no meaning. `check_laws.py` asserts the
stronger property that makes that safe -- on every body on disk, no two rules'
spans intersect. Disjoint deletions commute, so both the stripped text and the
reported flags come out the same whatever order the directory loads in.

Where a block has an optional part, write both whole forms and let one of
them miss -- `git-status.md` and `git-status-with-user.md` are mutually
exclusive, and which one hit is the survey's report of whether `Git user:`
was there. `background-session-*.md` are three such forms. Keep no form a
prefix of another: both would match, the shorter would leave a fragment
behind, and `check_laws.py` would fail on the resulting overlap.

Whole forms only work while the alternatives are few. Where the parts are
*independently* optional the count is the powerset, so split instead: one
rule per part, plus one for the frame that holds them.
`# Session-specific guidance` is a heading over five independently
switchable bullets, and it is six rules -- `session-specific-guidance.md`
is the heading and its leading blank line, the other five are bare list
lines. The heading rule matches the heading whether or not any bullet is
still there, so it does not depend on the bullet rules having fired; the
spans are merely adjacent, and adjacent deletions commute as freely as
distant ones. An unruled sixth bullet would survive without its heading,
which is ugly and loud -- the core digest moves and the survey shows a core
matching no fixture -- rather than quiet and wrong.

## Write the prose out; there is no whole-section hole

Templates here are literal, with holes only for what a session varies inside
one line or one paragraph. There is no placeholder meaning "the rest of this
section". `$...BLOCK` used to be one and was removed: its right-hand
delimiter was the next `# ` heading, a last section has none, and it ran to
end of body swallowing whatever followed
(`keying.claims.kb/this-proxy.kb/no-hole-may-cross-a-blank-line.md`).

So a section's rule is a transcript of that section, copied out of a masked
capture rather than typed. Upstream rewording therefore *breaks* the rule
instead of being absorbed by it, which is the point: the block stops
matching, its text stays in the core digest, and the survey shows a core
matching no fixture. Recopy the template from a current capture and re-run
`check_laws.py`.

## Deleting must leave the absent form byte-for-byte

A block rule's promise is that stripping it yields what a session that never
switched it on would have sent, so a template spans the blank line that
separates its block from the neighbouring one. A `# ` section takes that
separator on the *leading* side -- the template starts with `\n` and ends
after its own last content line -- because a block taking its trailing
separator would contend with the block after it for the same newline. A
list-item block (`- ...`) sits inside a list and has no separator to take.
