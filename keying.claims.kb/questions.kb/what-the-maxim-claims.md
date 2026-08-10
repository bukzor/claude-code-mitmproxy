---
label: Q_SILENCE
standing: agent
why:
    - ../obligation.kb/observability-ranks.md
    - ../obligation.kb/prefer-dissolving-to-checking.md
    - ../obligation.kb/price-of-dissolving.md
    - ../this-proxy.kb/the-block-overrun-fix-is-unmade.md
---

# Question 3: What Does "One Fewer Thing That Can Be Silently Wrong" Claim?

**As experienced.** A maxim offered as a justification, in the tone of
something self-evidently good -- the kind of sentence that ends a design
discussion rather than starting one.

**Well-posed.** Two questions wearing one coat:

1. *Is there an ordering on which "fewer silent things" is even
   meaningful?*
2. *Is the preference it asserts -- dissolve over check -- always right?*

**Finding on (1): yes, but weaker than the phrasing suggests.** There is a
total order on how an invariant can fail -- unrepresentable, loud,
checked, silent (`RANK`) -- and "fewer silent things" is a real
improvement in it. What there is *not* is a lattice: you cannot compose
two mechanisms and read off the rank of the combination, because a check
plus a check is not a better check, and a loud failure inside a silent
system is still a silent system. The negative result is stated in the
claim rather than papered over, and it is why the maxim licenses ranking
individual invariants and licenses no arithmetic on them.

**Finding on (2): no, it is conditional.** `DISSOLVE` prefers removing the
invariant to checking it, and `PRICE_OF_DISSOLVING` names the exception:
dissolution paid for with a representation nobody can read trades a
checkable obligation for an unreadable system, and that is a worse buy
than the check it replaced. The maxim is sound when the dissolution is
cheap in representation, which for the split it was -- the identity key is
*simpler* to read than the class key, not harder.

**The uncomfortable finding.** This ledger's own live counter-instance is
`BLOCK_FIX`: an invariant that two READMEs assert, that nothing checked,
and that was false on a fifth of the corpus. It was found by writing the
formalization -- by looking -- not by any loudness mechanism. The maxim
tells you what to do with an invariant once you have noticed it and is
silent about noticing, which is the harder half. Its real content, and the
reason it is worth keeping, is the instruction to *count* the silent ones;
in this repo that count went from unknown to one open item, and the
counting did that, not the preference.

**Settled by** `RANK` (the order, and that it is only an order),
`DISSOLVE` (the preference), `PRICE_OF_DISSOLVING` (the exception),
`SILENT_DEFAULT` (why the count starts high).

**Residue.** `BLOCK_FIX` is open, and the mechanism that surfaced it does
not run on a schedule.
