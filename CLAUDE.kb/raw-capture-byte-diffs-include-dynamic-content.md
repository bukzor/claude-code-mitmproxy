# Raw capture byte-diffs are contaminated by dynamic content

`system-prompts.kb/*.md` files (promoted from `prompt-captures/*.raw.md`
per the todo.md promotion step) are **raw**, unnormalized captures: they
retain whatever was live in that specific session — cwd, scratchpad
path, `git status`/recent-commits dump, and the model-id suffix (e.g.
`claude-sonnet-5` vs `claude-sonnet-5[1m]`). None of that is part of
the stable prompt template; all of it varies per capture regardless of
cc_version.

The `# Session-specific guidance` section is the same story one level
up: its bullet list is itself session-dependent (e.g. whether the `!`
bash-passthrough tip and the fork-subagent tip appear, vs. Agent/Explore
usage tips), not a fixed span that changes version-to-version.

Consequence: `diff`-ing two full-body captures (even same cc_version,
different sessions) mixes real template edits with this noise, and raw
byte-count deltas (`wc -c`) are not evidence of prompt-template growth
or shrinkage on their own — a capture with a longer git-status dump or
a present scratchpad section will simply be bigger, independent of any
actual prompt change.

Found while reviewing v2.1.202 vs v2.1.199 for "new sections": the two
headers cited as new (`# Executing actions with care`, `# Text output
...`) already existed verbatim at v2.1.199 — the growth was the dynamic
Environment block, not new template content. Same for the apparent
v2.1.202 -> v2.1.207 shrink. See
`.claude/ideas.kb/2026-07-08-000-Review-v2-1-202-*` for the full
writeup.

To review for genuine additive drift: diff the sections that are
*neither* `# Environment` nor `# Session-specific guidance`, or
normalize those loci first (blank the dynamic lines) before diffing.
