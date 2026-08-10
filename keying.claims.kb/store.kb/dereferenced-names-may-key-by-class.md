---
label: POINTER_KEYS
standing: bare
why:
    - name-by-identity-dedup-by-class.md
    - ../derivation.kb/drift-costs-what-the-key-decides.md
---

# A Name Nobody Recomputes May Key By the Class

`TWO_KEYS` reads as "never name by the quotient", and taken that way it
would condemn stores that are correct. The distinction it actually turns
on is `RECOMPUTED`'s: whether the name is *recomputed from content* on the
read path, or merely *dereferenced*.

- **Recomputed.** A reader takes a body, computes its key, and looks for
  it. A policy change moves the key, the lookup misses, and the store
  behaves as though the object were absent. This is the case `TWO_KEYS`
  governs, and there the key must be invariant.
- **Dereferenced.** A reader lists what is there, or follows a reference
  someone stored. The key is an opaque label. A policy change makes new
  entries land under new labels and does not touch old ones; nothing
  misses, because nothing is looked up by recomputation.

A quotient key is fine for a dereferenced name, and the drift is bounded
by `DRIFT_COST`: whatever transient decision the key drives gets re-decided
once. The canonical shape is a suppression key -- "have I already reported
this?" -- where a policy change costs exactly one repeated report and the
key is otherwise never computed twice against the same content.

The asymmetry has a tell that is easy to check: **can a reader arrive
holding the content rather than the name?** If yes, the key must be
invariant, because that reader will recompute. If the only way in is
through a listing or a stored reference, the class key is free.

**Smallest instance.** Two sibling stores, same digest function, opposite
verdicts: one is enumerated and its names are labels, so it may key by the
class; one is probed by content at write time, so it may not.

**What would kill it.** Someone adding a by-content lookup to the
dereferenced store -- a "find the entry for this body" helper. That one
function silently converts the store to the recomputed case, and the key
becomes wrong without changing.
