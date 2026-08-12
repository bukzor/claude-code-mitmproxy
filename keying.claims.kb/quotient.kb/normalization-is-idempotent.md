---
label: IDEMPOTENT
standing: bare
verify: .venv/bin/claude-mitmproxy-check-laws
---

# Normalizing a Normal Form Is a No-Op

The normalizer `n` induced by a rule set satisfies `n(n(x)) = n(x)`: it is
a retraction onto its image, and every normalized body is a fixed point.

This is what makes a normal form storable next to the body it came from.
Comparing a stored normal form against a freshly computed one is
meaningful; re-normalizing one is safe; a consumer handed either a body or
its normal form gets the same answer. Without idempotence none of those
hold and "the normal form" is not a thing, only "the normal form after `k`
passes".

It is not free, and it is not a theorem about rule sets in general. Each
rule rewrites what it matched to a form that is supposed to match the same
rule again and change nothing -- a rule that emitted text its own pattern
missed would keep moving. Worse, and likelier, one rule can emit text that
a *different* rule then matches, so the composite fails to be idempotent
while every rule is individually fine. That is why this is checked over
the whole corpus rather than argued.

**Smallest instance.** A rule whose pattern is a literal prefix followed
by a rest-of-line hole rewrites `<prefix><session value>` to
`<prefix>$HOLE`. Applied again, the hole matches the literal text `$HOLE`
and rewrites it to itself. Fixed point after one pass.

**What would kill it.** One body, anywhere in the corpus, where a second
pass differs from the first.
