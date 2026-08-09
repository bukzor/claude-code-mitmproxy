# Capture-digest masks

One file per mask, `<what-it-masks>.md`, holding a single template in the
same language as the system-prompt patches (`$PLACEHOLDER` holes in literal
prose -- spec: `~/.claude/system-prompt-patches.d/README.md`). Every
occurrence a mask matches is rewritten to the template *verbatim*, so each
placeholder's captured text becomes the placeholder's own name:

    body      - Primary working directory: /home/bukzor/claude/mitmproxy
    template  - Primary working directory: $CWD
    masked    - Primary working directory: $CWD

`incidents.content_hash` hashes the masked text, so two sessions that ran
the same prompt from different directories dedup to one capture.

## Why these live here and not in `~/.claude/`

The patches next door are one operator's preferences. Masks are the
capture system's identity function: a digest that varied with per-machine
state would not be content-addressed at all.

## A mask is a match template and nothing else

No `replace.md`, no `search.md`, no `upstream-removed.bool` -- the format
can't express them, deliberately.

The last two exist to make a miss loud, and a mask's miss is silent by
construction: masks run over tracebacks and subagent prompts too, where
matching nothing is the norm. Promising a warning that never comes is
worse than not promising one.

Dropping `replace` is the load-bearing one. Because the replacement is
always the template itself, a mask can only ever swap a placeholder's
captured span for that placeholder's name -- it *cannot* delete literal
prose. So a mask can't quietly shrink what the digest is able to notice,
and masking is idempotent: re-masking already-masked text is a no-op,
since the template matches its own output.

The corollary for authors: anything you want gone from the digest has to
sit inside a placeholder. `(1M context)` and the `[1m]` model-ID suffix
are removed by `model-id.md` only because its placeholders span the whole
model name and ID.

## Loudness is offline

A mask that stops matching is invisible in production -- the symptom is
every session minting a fresh digest, which nobody is watching. So
`check_masks.py` asserts, over the fixtures in `system-prompts.kb/`,
that every mask still matches at least one of them, that masking is
idempotent, and that no two fixtures collapse to one digest. Write a mask
only against text some fixture carries; if upstream ships a new volatile
region, promote a capture of it first (`system-prompts.kb/CLAUDE.md`).

## Editing

Masks compile once at proxy start, unlike patches, which are re-read per
request: a digest that changed mid-run would silently re-key everything
captured after it. After editing, restart the proxy and run
`rekey_captures.py` to bring `log/prompt-captures/` back in step.
