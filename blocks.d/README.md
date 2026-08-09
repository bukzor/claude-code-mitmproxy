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

They are never part of `incidents.content_hash`. Block *presence* is content:
a capture that carries `# Memory` is a different observation from one that
doesn't, and first-seen-wins dedup would throw the fuller one away.

## Blocks are stripped from the masked body

Masks run first, so a template here can be written against the tokens masks
leave behind rather than the volatile text they replaced -- `git-status.md` is
a dozen literal lines because `$GITBRANCH` and friends are already tokens by
the time it runs.

## Order-independent

Every block is tried against the result of the previous ones, but no rule may
*depend* on an earlier rule having fired: the set is loaded in filename order,
which is alphabetical and carries no meaning. Where a block has an optional
part, write both whole forms and let one of them miss -- `git-status.md` and
`git-status-with-user.md` are mutually exclusive, and which one hit is the
survey's report of whether `Git user:` was there.

## Deleting must leave the absent form byte-for-byte

A block rule's promise is that stripping it yields what a session that never
switched it on would have sent. Templates therefore span the block's blank-line
separators too: `# Memory\n$MEMORYBLOCK\n` consumes the heading, the body, and
the blank line before the next heading. A `$...BLOCK` placeholder matches the
rest of a top-level section (stopping before the next `# ` heading), which is
why these stay short and survive upstream rewording inside a section.

The corollary is a blind spot, and it's deliberate: copy that changes *inside*
a session-optional section doesn't move the core digest. The full `digest`
column still sees it, and the fixture is where that text is kept.
