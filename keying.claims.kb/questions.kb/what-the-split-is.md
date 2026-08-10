---
label: Q_STRUCTURE
standing: agent
why:
    - ../quotient.kb/an-invariant-name-must-be-injective.md
    - ../quotient.kb/the-equivalence-is-the-kernel.md
    - ../store.kb/name-by-identity-dedup-by-class.md
---

# Question 1: What Is the Structure Behind the Identity/Equivalence Split?

**As experienced.** "There are two digests you could file a capture under.
Filing by the raw one turned out better. What kind of thing is that
choice?" -- a question about a preference between two workable options,
expecting an answer of the form "here is the tradeoff and why this side of
it".

**Well-posed.** *Is there a naming function on bodies that stays adequate
as the rule set changes, and which functions are they?* Adequate meaning:
it never merges two bodies the rules in force call different.

**The finding is that these are not the same question.** The experienced
form presupposes a choice; the well-posed form has a theorem and no choice
in it. The adequate-under-every-admissible-rule-set names are exactly the
injective ones (`INJECTIVE`), because the empty rule set is admissible and
its partition is discrete. Filing by the bytes is not the better of two
options. It is the only option, and the other one was never a candidate --
it just took an argument to see that.

The rest follows and adds no commitments: the class question is real and
still needs answering, and `TWO_KEYS` observes that the question forbidden
as a durable key is precisely the one a rebuildable index may answer
freely. Two questions, two keys, and the second key is allowed to move
because nothing durable is named by it.

**Settled by** `INJECTIVE` (the theorem), `KERNEL` (why the class is not a
fact about the bodies), `TWO_KEYS` (the arrangement).

**Residue.** The theorem has one escape and it is not vacuous: promise the
rule set will only ever grow, and by `COARSEN` today's class name is
adequate forever. Nobody made that promise here, and mask edits have
happened, so the escape is closed by history rather than by argument. A
project that could honestly make the promise would be entitled to the
simpler design.
