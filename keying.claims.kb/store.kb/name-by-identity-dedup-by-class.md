---
label: TWO_KEYS
standing: bare
why:
    - ../quotient.kb/an-invariant-name-must-be-injective.md
    - ../derivation.kb/recomputed-keys-need-immutable-inputs.md
    - ../derivation.kb/whole-input-memos-cannot-go-stale.md
---

# The Store Asks Two Questions and Needs Two Keys

A content-addressed store answers two questions that look like one:

- **Which thing is this?** -- the name a stored object is filed under and
  referred to later.
- **Have we already got this?** -- whether a newly seen body adds anything
  to what is kept.

The first is durable and must survive policy change, so by `INJECTIVE` its
key is the body's identity. The second is a judgment about content and is
*meant* to move when the policy does -- that is what the policy is for --
so its key is the class. One key cannot be both: an invariant key cannot
express "same modulo session noise", and a class key cannot name anything
you intend to keep.

The arrangement that follows is forced, not chosen:

- The **name** is a function of the bytes. It never moves, so there is
  never a rename, so there is never a migration.
- The **dedup index** is a map from class to what is already held. It is
  *derived and never stored* -- rebuilt from the bodies, which are the
  only durable input. Nothing on disk can then disagree with the bodies,
  because nothing on disk restates them.
- The index is memoized under **the rule set object itself**, so by
  `WHOLE_INPUT` the memo cannot be stale in that component: a changed
  policy cannot compare equal to the old one, and equality is the whole
  test. No fingerprint, no timestamp, no regenerate command.

This is the level worth naming as a level: nothing here is a new
commitment. Every part is *definable* from the two priors, and its content
is the observation that they compose -- that the question forbidden as a
durable key is exactly the question a rebuildable index is free to answer.

**Smallest instance.** Rename a rule and re-run: not one stored file
changes name, and the index rebuilds itself on the next write with no
command issued.

**What would kill it.** A durable decision -- anything that outlives the
process -- taken on the index's answer rather than the name's. The split
holds only while the class key stays confined to the write-time question.
