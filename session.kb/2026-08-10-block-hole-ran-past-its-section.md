# 2026-08-10: `$...BLOCK` ran past its section on a fifth of the corpus

## How it surfaced

Not by any alarm, and not by looking for it. The day's work was the
identity/equivalence split (`38413ac`) and then writing its formal account
(`221fd7a`) — a claims ledger about what may key what. Stating the block
rules' invariant precisely enough to file it as a claim was what exposed
that nothing checked it and that it was false.

The operator then stated the rule that settles it in one clause: reject a
pattern that lacks both a left-hand and a right-hand delimiter.

## What was wrong

`$...BLOCK` meant "the rest of this top-level section", implemented as
`(?:(?!\n# ).)*` under `re.DOTALL` — bounded by the next `# ` heading. A
section that is *last* has no next heading, so the hole degenerated to a
trailing `.*` and swallowed everything after it.

Measured before removal: `scratchpad` ran to end of body in **20 of its 51
occurrences**, taking the trailing `gitStatus:` paragraph with it in 15.

Every other hole type is fine and for a reason worth keeping: `[^\n]*` is
bounded by the line break, `$LINES` by the blank line, and both of those
bounds always exist. Only a hole crossing blank lines has no delimiter it
cannot consume.

## Why nothing was loud

Over-deletion is silent by construction. Two distinct bodies collapse onto
one core digest, and the survey reports the second as already seen — the
same shape as a correct dedup. There is no signal to notice.

The mirror case is why the fix is affordable: a *literal* template can only
ever under-delete. When it under-deletes the block survives, the core digest
moves, and the survey shows a core matching no fixture. So the repair is not
a better bound, it is trading a silent failure mode for a loud one.

## What changed

`$...BLOCK` is deleted rather than repaired (`c84e683`), because no literal
repairs it: a greedy hole backtracks to its delimiter's *last* occurrence,
and the only literal that reliably opens a section is `\n# `, which would
hardcode into each block whatever section happens to follow it. The four
BLOCK templates became six literal transcripts — `background-session` has
three whole forms — at a cost of ~19KB of prose that breaks loudly on any
upstream reword.

Two things fell out on the way:

- The old `background-session.md` had no trailing newline and was leaving a
  stray blank line behind, violating the byte-for-byte promise. Separate
  defect, same neighbourhood, also unnoticed.
- Round-one templates took the *trailing* blank line and collided with
  `git-status-with-user`'s leading one. The pre-existing convention is
  leading, and `check_laws.py` caught the 1-byte overlap — the first thing
  in this area to fail loudly.

`check_laws.py` now asserts that no two block spans overlap, replacing a
weaker confluence check plus a flag-divergence warning. Disjoint deletions
commute, so disjointness gives order-independent stripped text *and* exact
flags at once.

The reasoning lives in `keying.claims.kb/this-proxy.kb/` —
`no-hole-may-cross-a-blank-line.md` (the rule) and
`block-spans-are-disjoint.md` (what the checker certifies).

## What stays open

The noticing. The mechanism that surfaced this — writing the invariant down
carefully enough to file it — does not run on a schedule, and the maxim the
ledger settles ("one fewer thing that can be silently wrong") is about what
to do with an invariant *after* you have noticed it.

Concretely, the same day's promotion survey turned up a live instance of the
same class: `# Session-specific guidance` has five session-optional bullets
and rules for only three, so a single build's two captures land on different
cores. That is
`.claude/todo.kb/2026-08-10-000-Session-specific-guidance-bullets-are-unruled-core-digest-noise.md`.
