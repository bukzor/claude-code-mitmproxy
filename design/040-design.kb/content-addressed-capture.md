---
why:
  - earned-silence
  - offline-validation
---

# Content-addressed capture

One mechanism (`incidents.py`) backs every "loud, exactly once": the
captured body is keyed by `content_hash` — sha256 over the text with
session-volatile regions (cwd, gitStatus, scratchpad path, cc_version,
…) masked — and both the body file and each per-rule record are
write-once by that key. Masking makes the key stable across sessions;
write-once makes warnings idempotent across proxy restarts. A persistent
mismatch on a proxy that patches every request warns on the first
request and never again — for that content.

The mask set is declarative templates in `masks.d/`, sharing the patch
compiler (`template-patch-model.md`), not regexes embedded in
`incidents.py`. They live in-repo rather than in `~/.claude/` alongside
the patches: patches encode one operator's preferences, but masks *are*
the capture system's identity function, and a digest that varied with
per-machine state would not be content-addressed at all. Three rules
differ from a patch's. A mask rewrites every occurrence, not the first.
A mask has no replacement text — the replacement *is* the template, so a
mask can only swap a placeholder's captured span for that placeholder's
name, never delete literal prose, and re-masking masked text is a no-op.
And a mask miss is never loud at proxy time: bodies include tracebacks
and subagent prompts, where finding nothing is the norm. Loudness moves
offline instead (`check_masks.py`, `loudness-policy.md`), so a typo'd
mask is caught as a dark rule rather than failing silent-and-open with
every session minting a fresh digest.

Masking neutralizes volatile *content*; it never deletes a
session-optional *block*. Block presence is part of the identity:
capture dedup is first-seen-wins, so a digest blind to whether this body
carried `# Memory` or the scratchpad section would discard the fuller
variant that promotion wants
(`../020-goals.kb/pristine-fixture-supply.md`) and would hide copy
changes *inside* a block behind the block's own optionality. Quotienting
blocks away is a survey-only view — `fixture-lifecycle.md`.

The same primitive serves failure capture (`log/patch-failures/`, verbatim
body + incident record) and fixture capture (`log/prompt-captures/`, verbatim
`.raw.md` plus its masked `.md` sibling — the normalization is already
computed for the digest, so materializing it doubles as a low-noise diff
target); only the directory layout and the promotion path differ.
