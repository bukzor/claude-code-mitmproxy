---
label: PROVENANCE
standing: agent
why:
    - recomputed-keys-need-immutable-inputs.md
    - ../obligation.kb/prefer-dissolving-to-checking.md
---

# Derived Data Travels With Its Provenance, or Is Not Stored

A value computed from inputs is stored together with the inputs it was
computed from, or it is not stored at all. Storing it bare turns every
later read into an unstated obligation -- "the inputs have not changed
since" -- which no reader can discharge and nothing detects.

Three arrangements, only the middle two admissible:

- **Bare derived value.** The obligation exists, is silent, and grows a
  companion artifact to check it (a version counter, an mtime, a
  "regenerate" command in a README). Rejected.
- **Value stored with its inputs.** Freshness becomes a comparison the
  reader can perform with no outside knowledge
  (`whole-input-memos-cannot-go-stale.md`).
- **Not stored; recomputed on demand.** The obligation cannot arise. Costs
  time, buys the strongest rank.

This is `DISSOLVE` applied to one recurring shape. The obligation is not
worth checking because it is so easy to delete: co-store the inputs, or
drop the cache.
