---
why:
  - earned-silence
---

# Content-addressed capture

One mechanism (`incidents.py`) backs every "loud, exactly once": the
captured body is keyed by `content_hash` — sha256 over the text with
session-volatile regions (cwd, gitStatus, scratchpad path, cc_version)
masked — and both the body file and each per-rule record are write-once
by that key. Masking makes the key stable across sessions; write-once
makes warnings idempotent across proxy restarts. A persistent mismatch
on a proxy that patches every request warns on the first request and
never again — for that content.

The same primitive serves failure capture (`log/patch-failures/`, verbatim
body + incident record) and fixture capture (`log/prompt-captures/`, verbatim
`.raw.md` plus its masked `.md` sibling — the normalization is already
computed for the digest, so materializing it doubles as a low-noise diff
target); only the directory layout and the promotion path differ.
