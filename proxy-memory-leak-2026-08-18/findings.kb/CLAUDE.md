# Findings

One evidence-backed conclusion per file; frontmatter per
`../findings.jsonschema.yaml` (`status` + `evidence` pointers).

Belongs: statements the investigation asserts, at any confidence --
including `open` questions framed as testable claims.
Does not belong: raw output (`../evidence.kb/`), candidate root causes
(`../root-cause.kb/` -- those compete; findings accumulate).

Update `status` in place as evidence lands; a refuted finding keeps its
file with `status: refuted` and a note on what refuted it.
