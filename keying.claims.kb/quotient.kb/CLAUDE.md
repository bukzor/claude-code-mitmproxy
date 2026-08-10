# quotient.kb -- maintenance guide

The algebra of "same, modulo what we agreed not to care about": a rule set
that normalizes bodies, the partition it induces, and what happens to that
partition when the rule set changes. Generic -- no storage here, no proper
nouns.

- `prior:` none
- `ontology:` body, rule, rule set, normalizer, occurrence, span,
  idempotent, fixed point, kernel, equivalence, class, partition, refine,
  coarsen, meet, discrete, name, injective, admissible, order-independence
- `defeated by:` a normalizer that is not idempotent, or an admissible
  rule-set change that refines rather than coarsens -- either one breaks
  the partition arithmetic every claim here computes with

## What belongs here

A property of normalization and the equivalence it induces, stated for an
arbitrary rule set over an arbitrary set of bodies.

## What does NOT belong here

- What a store does with the classes -> `../store.kb/`. This theory is one
  of that one's two priors.
- Why an unchecked property stays unnoticed -> `../obligation.kb/`. These
  theories are siblings; neither is a prior of the other, and a claim
  needing both vocabularies belongs downstream of both.
