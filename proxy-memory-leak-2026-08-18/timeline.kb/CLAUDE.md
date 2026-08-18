# Timeline events

One file per dated occurrence in the incident window (first symptom
through recovery). Names: `YYYY-MM-DD-NNN-slug.md`; frontmatter per
`../timeline.jsonschema.yaml`.

Belongs: anything that happened at a knowable time, with its source.
Does not belong: conclusions (`../findings.kb/`), raw captures
(`../evidence.kb/`), machine context (`../environment.kb/`).

Add a file when new evidence dates an event. Correct `at`/`confidence` in
place when better evidence lands -- events are interpretations, not
captures, so editing is fine.
