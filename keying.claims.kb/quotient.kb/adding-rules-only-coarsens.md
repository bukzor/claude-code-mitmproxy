---
label: COARSEN
standing: bare
verify: python3 check_laws.py
why:
    - the-equivalence-is-the-kernel.md
---

# Adding a Rule Merges Classes and Never Splits One

Order rule sets by inclusion and partitions by refinement. Growing the
rule set moves monotonically toward coarser: if `R ⊆ R'` then every class
of `P(R)` sits inside a class of `P(R')`. Two bodies the old rules called
different may become the same; two the old rules called the same can never
become different.

The intuition is that a rule deletes a distinction and deleting cannot
create one. The intuition is not a proof, because rules are applied in
sequence and each sees the text the previous ones left: a new rule changes
what the later rules match, and in principle that can manufacture a
difference between two bodies that previously normalized alike. So this is
a property of the rule set on the corpus, checked, not a theorem about
rule sets.

Why it is worth stating separately from `KERNEL`: it is the only thing
that makes the direction of policy drift predictable. Under monotone
growth, yesterday's classes are unions of today's -- never crossings --
so a stored class name is either still valid or has been absorbed into a
larger one. That is a much better failure mode than crossing, and it is
the premise the sole legitimate exception in `../store.kb/` runs on.

**Smallest instance.** Drop any single rule from the set and re-partition:
every class either stays put or splits. None crosses.

**What would kill it.** Two bodies that a smaller rule set normalizes
alike and the larger one separates -- one pair, anywhere in the corpus.
