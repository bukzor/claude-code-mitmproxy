---
label: RECOMPUTED
standing: bare
why:
    - ../obligation.kb/silence-is-the-default.md
---

# A Recomputed Key Must Be a Function of Immutable Inputs; a Dereferenced One Need Not

Two ways a stored name gets used, and only one of them constrains what the
name may depend on:

- **Recomputed** -- a reader takes an object in hand, computes what its
  name *would* be, and looks that up. Dedup, content-addressed lookup, and
  "have I seen this before?" are all this shape.
- **Dereferenced** -- a reader already holds the name, from a pointer
  stored alongside, and follows it. The name is never re-derived from the
  object.

A recomputed key must be a function of immutable inputs only. If the key
function is `k_P` for some policy `P`, then a store written under `P` and
read under `P'` answers "have I seen this?" with `k_P'` against names
minted by `k_P`, and every answer is wrong wherever the two disagree.
Nothing detects the disagreement: both sides are well-formed digests.

A dereferenced key may depend on anything at all, including a policy that
changes hourly, because the pointer preserves whatever correspondence
existed at write time. Policy drift cannot break a correspondence that is
never recomputed.

This is the criterion that decides where a mutable-policy key is
admissible, and it cuts finer than "content-addressing is good." It is
about the *read path*, not the write path.
