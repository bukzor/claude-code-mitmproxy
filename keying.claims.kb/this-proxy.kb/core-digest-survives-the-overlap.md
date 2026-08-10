---
label: CONFLUENT_TODAY
standing: bare
verify: python3 check_laws.py
why:
    - block-flags-are-an-artifact.md
    - ../quotient.kb/order-independence-is-a-separate-property.md
---

# The Core Digest Is Order-Independent Even Where the Flags Are Not

The same overlap that ruins the flags leaves the stripped text alone, and
the reason is worth having in writing, because it is why nothing had to be
fixed in a hurry.

The overlap is **containment**, not partial overlap. Run the container
first and both sections go in one deletion; run the contained rule first
and the container's pattern still reaches end of body and takes the rest.
Either way the same union of bytes is removed, so the text -- and
therefore the core digest `survey_captures.py` compares -- is identical.
It is the *credit* that is ambiguous, not the result.

This is checked, not argued from the shape. `check_laws.py` enumerates
orders exhaustively rather than sampling them: rules with disjoint spans
commute, so only the contested rules' relative order can matter, and that
is a handful of permutations rather than `12!`. An earlier sampling run
undercounted the affected bodies, which is the exact failure a sampled
check invites -- passing while the law is false.

So the two properties `blocks.d/README.md` conflates come apart cleanly
here: the deletion is confluent, the reporting is not. Any fix should
preserve the first while repairing the second, and a fix that changes the
stripped text would move every core digest in the corpus.

**What would kill it.** A second block pair overlapping *partially* rather
than by containment -- then the union removed would depend on order, the
core digest would move with a filename, and this claim would fail where
`FLAG_ARTIFACT` already does. `check_laws.py` asserts on exactly that.
