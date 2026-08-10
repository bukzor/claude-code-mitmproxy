---
label: LOSSY
standing: bare
why:
    - name-by-identity-dedup-by-class.md
    - ../quotient.kb/adding-rules-only-coarsens.md
    - ../obligation.kb/silence-is-the-default.md
---

# Keying by a Class Makes Every Policy Change a Migration That Cannot Always Succeed

Name a stored object by its class and the name moves whenever the rule set
moves. Every policy edit therefore owes a migration over everything
already stored. The cost people notice is that the migration is a chore.
The cost that matters is that **no total migration exists**.

Two failures, from opposite directions:

- **Coarsening collides.** By `COARSEN` the usual direction of a policy
  edit merges classes. When two stored objects land on one new name, the
  migration must discard one or abandon the naming. There is no third
  option: the name has less information than the objects, so the map is
  not injective and something has to go.
- **Refinement has no witnesses.** An edited rule can split a class. The
  survivor can be re-filed by recomputing from its bytes -- but the other
  members of its old class were never stored. Dedup discarded them at
  write time, back when the policy said they were the same. The
  distinction the refinement was written to draw is exactly the
  distinction the old policy already erased from the corpus.

So the honest statement of what is wrong with a single class key is not
"you have to run a script". It is: the script has a branch that deletes
data, and it must have that branch or be wrong. A migration tool for a
quotient-keyed store with no discard path is not a safer tool -- it is one
that has not noticed the collision yet.

Both losses are silent by construction (`SILENT_DEFAULT`). A discarded
duplicate leaves nothing behind that says a choice was made; the store
afterward is a perfectly consistent store of a slightly smaller world, and
no later reader can tell which world they are in.

**Smallest instance.** Add one rule that neutralizes a field two stored
bodies differ in. Re-derive names: one name, two files, and whichever the
migration keeps is now the only surviving evidence of either.

**What would kill it.** A store whose objects are pure class
representatives with nothing distinguishing to lose -- then the collision
discards a genuine duplicate and costs nothing. That is a store of
canonical forms, not a store of observations, and it should say so.
