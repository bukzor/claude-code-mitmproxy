---
label: INJECTIVE
standing: bare
why:
    - the-equivalence-is-the-kernel.md
    - adding-rules-only-coarsens.md
---

# A Name Adequate for Every Admissible Rule Set Is the Body's Identity

Call a naming function `v` **adequate** for a rule set `R` when it
separates whatever `R` separates: `n_R(a) ≠ n_R(b)` implies
`v(a) ≠ v(b)`. Equivalently, `ker(v)` is contained in `P(R)`. An
inadequate name collapses two bodies that the rules in force call
different, and no later work can tell them apart again.

Now require a *fixed* name that stays adequate across every rule set in
the admissible set `A`. Then

```
ker(v)  ⊆  ⋀ { P(R) : R ∈ A }
```

the meet of the induced partitions -- the relation "no admissible rule set
tells these two apart".

The theorem is what that meet turns out to be. The empty rule set is
admissible: removing rules is a thing one does, and with no rules the
normalizer is the identity, so `P(∅)` is the discrete partition. A meet
containing a discrete member is discrete. Therefore `ker(v)` is equality
and **`v` is injective** -- the name is a faithful function of the bytes,
which is to say it is the body's identity and not any equivalence class's.

This is not a preference between two reasonable keys. Given that a rule
may be removed, injectivity is forced; the only way to want a class name
instead is to give up adequacy across policy change, and giving that up
has a price that is paid elsewhere and in full
(`../store.kb/quotient-keys-make-lossy-migrations.md`).

**The one escape, stated precisely.** Bound `A` to rule sets that only
ever grow from the current `R₀`. By `COARSEN` every such `P(R)` is coarser
than `P(R₀)`, so the meet is attained at `R₀` itself, and today's class
name is adequate forever. The escape is real and it is narrow: it is void
the first time a rule is deleted, and equally void when a rule is
*edited*, since an edit is not growth and can refine. Anyone claiming this
escape is promising an append-only rule set out loud.

**Smallest instance.** Two bodies alike but for one masked path share a
class today. Delete that rule and they are two classes. A name drawn from
the class was adequate before the deletion and is not after; a name drawn
from the bytes was adequate both times, and would still be adequate under
a rule set nobody has written yet.

**What would kill it.** A demonstration that the admissible rule sets are
genuinely bounded below by some `R₀` that will never be weakened or
rewritten -- which is a promise about the future, not an observation, and
so is the kind of thing that gets made carelessly.
