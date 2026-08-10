# keying.claims -- what may key what

The formal account behind three questions: what the identity/equivalence
split *is*, what not doing it costs, and what the maxim "one fewer thing
that can be silently wrong" actually claims. Claims live one per file in
`keying.claims.kb/`; this page carries the shape and the picture.

## The poset

Not a chain. `derivation` and `quotient` are independent -- one is about
values computed from values, the other about equivalence under a rule set
-- and they first need each other in `store`.

```
obligation ──► derivation ──┐
                            ├──► store ──► this-proxy ──► questions
quotient ───────────────────┘
```

| theory | holds | defeated by |
|---|---|---|
| `obligation` | why an unchecked invariant stays unnoticed, and the four ranks of failure | an obligation cheap to check whose dissolution needs a representation nobody can read |
| `derivation` | what a key may be a function of; when a memo can go stale | a policy that is genuinely immutable |
| `quotient` | the algebra of "same modulo what we ignore" | a normalizer that is not idempotent, or an admissible change that refines |
| `store` | naming, dedup, migration | an append-only rule-set promise actually kept |
| `this-proxy` | the generic claims discharged against this repo | restructuring the repo -- this one is meant to be thrown away |
| `questions` | the three questions, stated twice each | a question whose two forms coincide |

## The picture

A body arrives and two questions are asked of it that look like one:
**which thing is this**, and **have we got this already**.

The second is answered by a rule set that normalizes away session noise.
That defines an equivalence -- the kernel of the normalizer, and nothing
else (`KERNEL`). There is no rule-set-independent fact about two bodies
being "really the same" that the rules are approximating; change the rules
and you have a different relation, not a better estimate of one.

So a name drawn from the class moves when the rules move. Ask whether any
name survives every admissible rule set and the answer is a theorem: the
empty rule set is admissible, its partition is discrete, a meet with a
discrete member is discrete, and therefore the name must be **injective**
(`INJECTIVE`). Keying by the bytes is not the better of two options. It is
the only one.

Ignore that and the bill comes as a migration on every policy edit, which
is where the second question's real answer lives: **no total migration
exists** (`LOSSY`). Coarsening -- the usual direction -- collides two
stored objects onto one name and something must be discarded; refinement
splits a class whose other members were dropped at write time and are
gone. The rekey script's trash-the-duplicates branch was the theorem,
compiled. The cost was never the chore.

What replaces it is forced rather than designed (`TWO_KEYS`): the durable
name takes the invariant key, and the question forbidden as a durable key
becomes an index that is *derived and never stored*. Memoize that index
under the rule set object itself and by `WHOLE_INPUT` the memo cannot be
stale in that component -- a changed policy cannot compare equal to the
old one, so a rule edit needs no follow-up command. Only in that component
(`COVERAGE`); the uncovered one is discharged by an ownership argument
stated out loud (`DIR_OWNERSHIP`).

The prohibition is narrower than it sounds. A name nobody recomputes from
content may key by the class (`POINTER_KEYS`), and the damage is bounded
by what the key decides (`DRIFT_COST`). The rule to carry is not "never
key by a mutable policy" but **never let a mutable policy name anything
you intend to keep**.

And the split fixed naming, not retention (`RETENTION`). Dedup still keeps
one body per class, so which member survives still depends on arrival
order. Deliberate -- the alternative is unbounded -- and it means the
store answers "what distinct content was seen" soundly and "which variant
is typical" not at all.

## What was compartmentalized away, and what it cost

- **Masking as a single endomap.** It is a composition with a fixed order,
  and idempotence of the composite says nothing about order
  (`ORDER_FREE`). If one rule ever feeds another, the normalizer stops
  being a function of the rule *set* and `COARSEN` -- which quantifies
  over subsets -- becomes ill-typed. Paid for by checking `COARSEN`
  directly: the consequence, not the mechanism.
- **Bodies as opaque strings.** Blocks see a body as a sequence of
  sections, and that structure is exactly where the one live defect sits
  (`FLAG_ARTIFACT`). The cost is that the bug is unstatable above
  `this-proxy`: anyone reusing these claims on structured documents gets
  no warning from them.
- **The admissible rule sets as unbounded.** This is the premise doing all
  the work in `INJECTIVE`. It is history, not necessity -- a project that
  could honestly promise an append-only rule set would be entitled to the
  simpler design.
- **Blocks and masks as the same kind of rule set.** They are not: masks
  rewrite, blocks delete, and only blocks have consumed *reporting*.
  `check_laws.py` checks idempotence and monotonicity for masks only.
  Deliberate -- blocks name nothing durable, so `DRIFT_COST` bounds the
  exposure at one recomputed survey column.
- **Digest equals identity.** Collisions ignored throughout, noted so the
  gap is not rediscovered as a finding.

## The answers, in one line each

1. **What the split is** (`Q_STRUCTURE`) -- not a preference. Injectivity
   is forced by the possibility of deleting a rule.
2. **What not splitting costs** (`Q_HARM`) -- not effort. A migration that
   cannot always succeed, losing data in both directions of policy change.
3. **What the maxim claims** (`Q_SILENCE`) -- a real total order on
   failure modes, but not a lattice, and a preference with a stated
   exception. Its useful content is the instruction to *count* the silent
   invariants; the counting, not the preference, is what found `BLOCK_FIX`.

## Scanning

```sh
grep -rl 'standing: open'  keying.claims.kb/   # undecided, needs a ruling
grep -rl 'standing: agent' keying.claims.kb/   # my call, veto invited
grep -rh '^verify:'        keying.claims.kb/ | sort -u
```
