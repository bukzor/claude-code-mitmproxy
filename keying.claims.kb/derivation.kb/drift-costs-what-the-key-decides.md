---
label: DRIFT_COST
standing: bare
why:
    - recomputed-keys-need-immutable-inputs.md
---

# Policy Drift Costs Exactly What the Key's Decision Costs to Redo

`RECOMPUTED` forbids mutable-policy keys on the read path, which sounds
absolute and is not. The damage a drifting key does is bounded by the
decision it drives, so price the decision:

- **Durable decisions** -- what a stored artifact is *named*, which of two
  observations is kept, where a file lands. Redoing these means a
  migration over everything already stored, and the migration can fail
  (`../store.kb/quotient-keys-make-lossy-migrations.md`).
- **Transient decisions** -- whether to emit a warning, whether to skip
  work that is safe to repeat. Redoing these costs one repeat.

A quotient key driving a transient decision is fine and needs no
apology: the worst a policy change does is make the system re-decide, and
re-deciding is what the decision is for. A quotient key driving a durable
name is the error `RECOMPUTED` names.

So the rule to carry is not "never key by a mutable policy" but "never let
a mutable policy name anything you intend to keep."
