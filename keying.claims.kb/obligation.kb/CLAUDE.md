# obligation.kb -- maintenance guide

When a system may leave a requirement unchecked, and what to do instead of
checking it. The most generic theory here: nothing in it mentions keys,
digests, or this repo.

- `prior:` (none)
- `ontology:` invariant, obligation, violation, detector, observability,
  loud, checked, silent, dissolve, representation, cost
- `defeated by:` an obligation whose check is cheap and whose dissolution
  requires a representation nobody can read

## What belongs here

A claim about the *status* of a requirement -- who or what would notice it
failing -- stated without reference to what the requirement is about.

## What does NOT belong here

The requirement itself. "Names must survive a mask edit" is a claim about
keys and belongs downstream; "an unchecked requirement is silent by
default" belongs here.
