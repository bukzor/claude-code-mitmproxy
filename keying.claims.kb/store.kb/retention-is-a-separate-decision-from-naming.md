---
label: RETENTION
standing: agent
why:
    - name-by-identity-dedup-by-class.md
    - quotient-keys-make-lossy-migrations.md
---

# Naming Was Made Policy-Independent; Retention Was Not

`TWO_KEYS` fixes the naming problem completely and the retention problem
not at all, and it is worth saying so out loud, because the arrangement
looks finished and is not.

Under it a store names by identity and *keeps* by class: the second body
in a class is never written. So which member of a class survives is
whichever arrived first. Two runs over the same traffic in a different
order produce stores that agree on every name and disagree on which bodies
are in them. The name is order-independent; the contents are not.

That is a real residue of the first failure in `LOSSY` -- the write-time
one -- and the split does nothing about it. A refinement of the rules
still cannot be applied retroactively, because the members that would
witness it were dropped at write time and identity naming does not bring
them back.

**And it should stay this way.** The alternative is retaining every body,
which is unbounded in exactly the dimension that grows without limit --
one observation per request, most of them identical. Retention by class is
a deliberate, priced loss: bounded storage in exchange for a corpus that
reflects the policy in force when each body arrived, and an arrival order
baked into what is on disk.

What the pricing buys, and what it does not: the store is a sound source
of *distinct observed content* and an unsound source of *frequency* or of
*which variant is typical*. Any question of the second kind asked of this
store gets a confident answer about arrival order instead.

**What would kill it.** A retention rule that does not consult the
policy -- keeping one body per identity with a bound enforced some other
way (age, count, sampling). Then naming and retention would both be
policy-independent, and this claim would be about a design nobody runs.
