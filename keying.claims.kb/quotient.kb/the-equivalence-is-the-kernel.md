---
label: KERNEL
standing: bare
why:
    - normalization-is-idempotent.md
---

# "Same Content" Is the Kernel of the Normalizer, and Nothing Else

Two bodies are equivalent exactly when their normal forms are equal:
`a ~ b` iff `n(a) = n(b)`. Being a pullback of equality, this is an
equivalence relation for free -- there is nothing to prove and nothing to
get wrong -- and it partitions the bodies into classes.

The content of the claim is the "and nothing else". There is no
rule-set-independent fact about two bodies being *really* the same modulo
session noise, waiting to be approximated better as the rules improve. The
relation is defined by the rule set; change the rule set and you have a
different relation, not a better estimate of the same one. Talk of the
rules "getting more accurate" smuggles in a target relation that does not
exist.

Two consequences that later claims lean on. A digest of the normal form is
a *name for a class*, not a name for a body -- it denotes the class, and
which class that is depends on the rule set in force when the digest was
taken. And the class has no member distinguished from the others: any
member normalizes to the same thing, so a store holding one member has
thrown the others away with no record of what it discarded.

**Smallest instance.** Two bodies differing only in one filesystem path
are one class today. Nothing intrinsic to them says so. A rule neutralizes
that path; that rule is the entire reason.

**What would kill it.** A place in the system where two bodies are treated
as the same content while their normal forms differ -- that would be an
equivalence the kernel does not capture, and the claim would be false as
stated.
