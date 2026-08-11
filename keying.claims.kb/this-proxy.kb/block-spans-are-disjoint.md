---
label: DISJOINT
standing: bare
verify: python3 check_laws.py
why:
    - no-hole-may-cross-a-blank-line.md
    - ../quotient.kb/order-independence-is-a-separate-property.md
---

# No Two Block Rules Delete the Same Bytes

On every body on disk -- captures, subagent captures, promoted fixtures --
no two `blocks.d/` rules have intersecting deletion spans. `check_laws.py`
asserts it.

This is worth checking as one property because it carries two. Disjoint
deletions commute, so disjointness gives order-independence of the stripped
text -- the load order is alphabetical and carries no meaning, so a core
digest that moved with it would be an artifact of a filename -- and it gives
exactness of the reported flags, since no rule can consume a region another
rule was going to claim. `blocks.d/README.md` used to state those as one
promise and they came apart; now they are two consequences of one
measurement.

It replaces a weaker argument. Under `$...BLOCK` the overlap was real but
was always *containment*: an overrunning `scratchpad` span strictly
contained `git-status-with-user`'s, so the same union of bytes was removed
whichever ran first. The text was confluent and only the credit was
ambiguous. Removing the placeholder removed the overlap itself, which is
strictly more than fixing the flags would have been.

**What would kill it.** Two templates that legitimately share bytes: a
session-optional region nested inside another, or -- the live risk as whole
forms accumulate -- two forms of the same block where one's literal text is
a prefix of the other's, so both match and the shorter leaves a fragment
behind. `background-session` already has three forms. Nothing prevents this
structurally; the check is what would catch it.
