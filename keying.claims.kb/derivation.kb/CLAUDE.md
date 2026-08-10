# derivation.kb -- maintenance guide

Rules about values computed from other values: when the computed value may
be stored, what its key may depend on, and when a memo can go stale.
Generic -- no algebra of equivalence here, and no proper nouns.

- `prior:` `../obligation.kb`
- `ontology:` input, policy, derivation, derived value, key, name,
  provenance, recomputation, dereference, staleness, memo, coverage,
  ownership, transient, durable
- `defeated by:` a policy that is genuinely immutable, which makes keying
  by it free and every claim here vacuous

## What belongs here

A constraint on the *shape* of a derivation-and-storage arrangement,
stated without reference to what is being derived.

## What does NOT belong here

- Why a violation goes unnoticed -> `../obligation.kb/`. Cite it.
- What masking in particular does -> `../quotient.kb/`. These theories are
  siblings; neither is a prior of the other.
