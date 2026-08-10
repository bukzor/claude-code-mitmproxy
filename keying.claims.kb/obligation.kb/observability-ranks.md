---
label: RANK
standing: agent
why:
    - silence-is-the-default.md
---

# Observability Ranks, and Why It Is Not a Lattice

An invariant occupies exactly one of four ranks, by what it takes for a
violation to be seen:

- **unrepresentable** -- the violating state cannot be constructed; the
  invariant is a theorem about the representation rather than a constraint
  on a value.
- **loud** -- violation reports itself at the moment it occurs.
- **checked** -- violation is caught by a check someone has to run.
- **silent** -- violation is observable only to an audit nobody scheduled.

The ranks are totally ordered by the work a violation costs before it is
noticed, and that is the whole structure: a ranked scale, an ordinal.

It is *not* a lattice, and calling it one would be the empty kind of
naming. A lattice needs meet and join that mean something, and here they
do not: two invariants at different ranks have no natural combination that
is itself an invariant at a computed rank. Composite systems do not
combine ranks pointwise either -- a loud check guarding a silent invariant
leaves the pair silent whenever the guard is skipped, which is a
containment fact about execution paths, not a join. The scale earns its
place by ordering single invariants; it claims nothing about composing
them.
