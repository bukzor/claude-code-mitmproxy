# CLAUDE.kb — deferred companion to the root CLAUDE.md

Durable design and reference knowledge about this project's internals (and the
dependencies it leans on) that a future agent should read *before* touching the
relevant area — but that isn't needed every conversation, so it stays out of the
always-loaded root `CLAUDE.md`.

One topic per file, prose, kebab-case names. No frontmatter/schema.

Belongs here: non-obvious, durable facts — protocol shapes, where things really
live, gotchas grounded in source/experiment.

Does not belong: task breakdowns (`.claude/todo.kb/`), captured payloads
(`system-prompts.kb/`), or unconditional maintenance rules (root `CLAUDE.md`).
