---
label: COVERAGE
standing: bare
why:
    - whole-input-memos-cannot-go-stale.md
---

# A Memo Is Stale-Proof Only in the Components Its Key Covers

`WHOLE_INPUT` is stated for the whole input and is routinely applied to
part of one. Where `f(a, b)` is memoized under key `a` alone, the memo is
stale-proof in `a` and unprotected in `b`; changes to `b` are exactly as
invisible as any proxy key's blind spot. The claim survives, its scope
does not.

An uncovered component is admissible, but only against an explicit
**ownership argument**: some party is the sole mutator of `b`, and that
party updates the memo on every mutation. That argument is a real premise
with a real failure mode -- a second writer, a human editing the store by
hand, a recovery procedure -- and it should be written down where the memo
is defined, since nothing about the code will suggest it.

The discipline this yields: when reading a memo, enumerate the components
of the derivation's input and mark each covered or owned. A component that
is neither is a silent invariant wearing a cache's clothing.
