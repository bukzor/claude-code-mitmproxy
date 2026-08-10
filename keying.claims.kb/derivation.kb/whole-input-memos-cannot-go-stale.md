---
label: WHOLE_INPUT
standing: bare
why:
    - store-provenance-or-store-nothing.md
---

# A Memo Keyed on Its Whole Input Cannot Go Stale

Store `(x, f(x))` and look up by comparing `x`. For deterministic `f`,
either the held `x` equals the current one -- and the held value is
correct, by determinism -- or it does not, and you recompute. There is no
third state, so "stale" is not a state the memo can be in.

Staleness requires a *proxy* key: a timestamp, a modification time, a
version counter, a hash of part of the input, a flag someone sets. Every
one of these can agree while the input differs, and that gap is the only
place staleness lives. Remove the proxy and the gap closes.

The price is that the key must be as large as the input and comparable by
value; where the input is huge or has no equality, a proxy is forced and
the obligation comes back. Where the input is small and structural -- a
tuple of records, a parsed rule set -- the whole-input memo is available
and there is no reason to take the proxy.

Note what this does *not* buy: coverage
(`memo-coverage-is-per-component.md`).
