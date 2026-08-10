---
label: ORDER_FREE
standing: agent
why:
    - normalization-is-idempotent.md
    - adding-rules-only-coarsens.md
    - ../obligation.kb/prefer-dissolving-to-checking.md
---

# Order-Independence Is Not Idempotence, and Is Only Sometimes Owed

A normalizer built from a rule set is a *composition*, and the composition
fixes an order -- usually an accident of how the rules are enumerated.
Idempotence of the composite says nothing about whether that order
matters: `n` can be a perfectly good retraction whose image depends on
which rule ran first. They are different laws and each has to be argued
separately.

Two rules commute when their matched spans are disjoint on every body,
because deleting or rewriting disjoint spans gives the same result in
either order. So order-independence is decidable directly from the spans,
and the rules whose spans overlap somewhere are the only ones whose
relative order can matter -- which also makes an exhaustive check cheap,
since the orders worth enumerating are the orders of the contested few.

**Whether you owe the property depends on who reads the order.** Where
some *result* is named by which rule fired, or where the enumeration order
is alphabetical and therefore an artifact of filenames, order-independence
is load-bearing and must be checked. Where the composite has one consumer
that always runs the same fixed order, a difference between orders is
unobservable, and a check for it guards nothing: by `DISSOLVE` that check
is cost without a rank change, and should not exist.

The interesting case is the one in between: you fear rule interaction, but
what you actually depend on is a *consequence* of non-interaction, not
non-interaction itself. Check the consequence. `COARSEN` is exactly this
-- the hazard is one rule feeding another, and the check is the
partition-level property that hazard would break, which is both cheaper to
state and closer to what would hurt.

**What would kill it.** A second consumer applying the rules in a
different order, which would turn the unobservable difference into a
disagreement between two callers and make the unowed check owed.
