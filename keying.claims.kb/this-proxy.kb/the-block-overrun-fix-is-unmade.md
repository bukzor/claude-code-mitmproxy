---
label: BLOCK_FIX
standing: open
why:
    - block-flags-are-an-artifact.md
    - core-digest-survives-the-overlap.md
---

# Which Repair the Block Overrun Gets Is Undecided

`FLAG_ARTIFACT` is measured and `CONFLUENT_TODAY` bounds the damage. What
to do about it is a design call nobody has made, and it should not be made
by whoever next touches the file.

Three repairs, each conceding something different:

- **Bound `$...BLOCK` at a blank-line-separated paragraph** instead of at
  the next `# ` heading. Fixes the cause. Changes what every existing
  block rule matches, so it moves core digests across the corpus and needs
  every `blocks.d/` rule re-read against real bodies.
- **Make overlap loud in `strip_blocks`.** Cheapest, and it turns a silent
  wrong answer into a checked one -- `RANK`'s middle band. Leaves the
  flags wrong; it only stops them being quietly wrong.
- **Report every rule whose pattern matched, before deleting anything.**
  Makes the flags mean "was present", which is what both READMEs already
  claim they mean, and leaves the deletion untouched, so no digest moves.
  Costs a second pass over the body per rule.

The third looks best on the stated criteria -- it repairs the documented
promise and moves nothing -- and it is not obviously right, because it
makes "present" and "deleted" different sets, and some later reader will
assume they are the same. That is the tradeoff to rule on.

Settled by: an operator ruling. Until then `check_laws.py` warns and the
promise in `blocks.d/README.md` stays false; the honest interim move, if
this sits, is to correct the README rather than let it keep claiming a
property the code does not have.
