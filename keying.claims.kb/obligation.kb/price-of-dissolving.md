---
label: PRICE_OF_DISSOLVING
standing: agent
why:
    - prefer-dissolving-to-checking.md
---

# Dissolving Has a Price, and Sometimes It Is Too High

Dissolution buys silence-proofing with representation complexity, and the
trade is not always worth taking. Where the check is cheap, re-runnable,
and already part of a routine someone performs anyway, and where the
representation that would make the violation unrepresentable is harder to
read than the invariant it enforces, checking wins.

The worked case is masking idempotence
(`../quotient.kb/normalization-is-idempotent.md`). Nothing in the
representation prevents someone writing a mask whose output re-matches
differently; making that unrepresentable would mean constraining the
template language until the property held by construction, which is a
large change to a small, legible format. Instead an offline check asserts
it over the whole fixture set. That is rank `checked`, deliberately, and
the note is that it *was* a choice rather than an oversight.

So `DISSOLVE` is a default with a stated exception, not a law. The
exception has to be argued at the point it is taken; an unargued
`checked` is just the cheaper edit wearing this claim as cover.
