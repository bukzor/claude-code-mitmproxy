---
label: Q_HARM
standing: agent
why:
    - ../store.kb/quotient-keys-make-lossy-migrations.md
    - ../store.kb/retention-is-a-separate-decision-from-naming.md
    - ../derivation.kb/drift-costs-what-the-key-decides.md
---

# Question 2: What Is Wrong With Not Doing the Split?

**As experienced.** "Keying by the masked digest worked. It just meant a
rekey script had to run after a mask edit. What is actually wrong with
that?" -- a question about a chore, expecting an answer about effort,
forgetting to run things, and friction.

**Well-posed.** *Does a total migration exist?* That is: for an arbitrary
change to the rule set, is there a map from the old store to the new one
that loses nothing?

**The finding is that the honest answer is about information, not
effort.** No such map exists (`LOSSY`). The usual direction of a policy
edit merges classes, and a merge means two stored objects want one name,
so the migration must discard. The rekey script's trash-the-duplicates
branch was never a rough edge to polish -- it is the theorem, compiled. A
migration tool for a quotient-keyed store *without* a discard path is not
a cleaner tool; it is one that has not met a collision yet.

So the chore framing understates it in the specific way that matters: a
chore you skip costs you the chore, and this one, run correctly, still
costs data. The split removes the migration entirely -- not by automating
it, by making the name unable to move.

The severity is not uniform, and `DRIFT_COST` says where the line is: a
quotient key driving a *transient* decision costs one repeated decision
and is fine (`POINTER_KEYS`). What is forbidden is letting a mutable
policy name something you intend to keep.

**Settled by** `LOSSY` (no total migration), `TWO_KEYS` (what replaces
it), `DRIFT_COST` and `POINTER_KEYS` (the bound, and the legitimate
exception).

**Residue, and it is substantial.** `LOSSY` names two losses and the split
only removes one. The write-time loss stands: dedup still keeps one body
per *class*, so the members that would witness a future refinement are
still discarded as they arrive, and which member survives still depends on
arrival order (`RETENTION`). That is deliberate -- the alternative is
unbounded -- but it means the store answers "what distinct content was
seen" soundly and "which variant is typical" not at all.
