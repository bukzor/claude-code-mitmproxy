---
why:
  - earned-silence
  - offline-validation
---

# Content-addressed capture

One mechanism (`incidents.py`) backs every "loud, exactly once": the
captured body is keyed by `masked_hash` — sha256 over the text with
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
target). They differ in the promotion path, the directory layout, and how
many keys they need.

## Identity and equivalence are separate keys

`masked_hash` answers "is this the same content, modulo how this session
happened to differ?" — and its answer moves whenever `masks.d/` does. That
is exactly what a *dedup* key should do and exactly what a *file name* must
not: naming stored artifacts by a mutable policy's output invalidates a
whole directory on every edit to that policy.

`log/prompt-captures/` is where that bites, because it is the curated store
— surveyed, promoted from, diffed by hand. So its two questions get two
keys:

- **Identity** is `digest_of` over the body exactly as sent. It names the
  file, and no mask edit can invalidate it. The store is append-only in
  consequence: nothing is renamed, and no observation is discarded to free
  up a name.
- **Equivalence** is `masked_hash`, demoted to an in-memory set of the
  masked digests already on disk, which `syscapture.py` derives from the
  `.raw.md` files themselves. The set is cached against the mask set it was
  taken under, and that mask set is re-read per request anyway, so a
  `masks.d/` edit invalidates the cache by inequality — no separate
  staleness signal to compute, no command to remember. Rebuilding reads the
  whole store and costs tens of milliseconds, once per proxy start and once
  per mask edit; the same pass rewrites any masked `.md` sibling whose text
  the edit changed.

The index is derived, never stored, so the raw bodies stay the single
durable input and nothing on disk can contradict them. The cost is that a
capture dropped into the directory by hand mid-run is invisible until the
next rebuild — acceptable, since the directory is written by the proxy.

`log/patch-failures/` keeps one key, and the asymmetry is deliberate.
Nothing surveys it and nothing promotes from it, so a name there is only
ever read by the record pointing at it — and a record and its body are
written together under one digest, so the pair stays internally consistent
whatever masks later become. The one thing a mask edit changes is that a
still-live failure warns once more, which is the right answer: you changed
what "the same failure" means.
