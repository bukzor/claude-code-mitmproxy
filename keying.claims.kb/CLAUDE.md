--- # workaround: anthropics/claude-code#13003
depends:
    - Skill(llm-claims)
    - Skill(llm-claims-kb)
---

# keying.claims.kb -- maintenance guide

What may key what, and what a key may be a function of. One theory per
collection, one claim per file, label and standing in frontmatter.
`../keying.claims.md` is the reader's entry point and carries the poset.

## What belongs here

A commitment about derivation and keying whose reversal would change how
this repo stores things: the algebra masking obeys, the rule a stored name
answers to, the reason a given invariant is allowed to go unchecked.

## What does NOT belong here

- What the code currently does -> `../design/040-design.kb/`. That
  collection is descriptive; this one is contestable. Where they overlap,
  design.kb states the behavior and cites nothing, and a claim here states
  why that behavior is forced.
- Procedure -> `../CLAUDE.kb/`. A directive is not a claim; dressing one in
  `standing:` produces a file that says nothing about its own standing.

## Filing a new claim

Placement is fixed by vocabulary, not topic (`Skill(llm-claims)` §
Theories): a claim goes in the earliest theory whose ontology -- its own
plus its priors' -- admits every word the claim needs. `this-proxy.kb` is
the only collection admitting proper nouns, and is the one to throw away
when the repo is restructured.

Each collection's `CLAUDE.md` carries its theory header: `prior:`,
`ontology:`, `defeated by:`.
