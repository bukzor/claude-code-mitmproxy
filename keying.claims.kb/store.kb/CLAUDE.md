# store.kb -- maintenance guide

Where the two priors meet: a store that keeps bodies, names them, and
decides which ones to keep. `derivation.kb` says what a key may be a
function of; `quotient.kb` says what the classes do under policy change;
neither alone can say what a capture store should be keyed by.

- `prior:` `../derivation.kb`, `../quotient.kb`
- `ontology:` capture, store, name, retention, dedup, representative,
  arrival order, append-only, migration, index, rebuild, namespace
- `defeated by:` an append-only rule-set promise actually kept -- the
  narrow escape `INJECTIVE` names. Under it a class name is adequate
  forever, and every claim here collapses to "either key works"

## What belongs here

A commitment about how stored things are named, kept, or discarded, that
needs both an equivalence and a derivation to state.

## What does NOT belong here

- Which directory, which digest, which script -> `../this-proxy.kb/`.
  Claims here are about stores, not about this one.
