---
label: FLAG_ARTIFACT
standing: bare
verify: python3 check_laws.py
why:
    - ../quotient.kb/order-independence-is-a-separate-property.md
---

# The Block Flags Name Whoever Ran First, Not Who Was There

`blocks.d/README.md` says no rule may depend on an earlier rule having
fired, and `design/040-design.kb/fixture-lifecycle.md` says the per-row
block flags *are* the names of the rules that fired, so flags and stripper
cannot drift apart. Both are false on real bodies, and this is the
measurement.

The mechanism is one pattern. `BLOCK_PATTERN` in `templates.py` is
`(?:(?!\n# ).)*` -- it ends at the next top-level heading, and when its
section is the body's last it runs to end of body. Anything after that
section which is *not* introduced by a `# ` heading is inside the span. In
subagent bodies the `# Scratchpad Directory` section is last and
`gitStatus:` follows it as a bare paragraph, so `scratchpad`'s span
strictly contains `git-status-with-user`'s. Whichever rule runs first
takes the credit; the other reports nothing, having found nothing left.

The overlap is a single containing pair, not a tangle: one rule pair, and
containment rather than partial overlap, on every affected body.

**Blast radius, as of this writing** (`check_laws.py` prints the current
figures). Of 55 main captures, 31 carry a scratchpad section and **none**
has it last -- a later `# ` heading always stops the span. Of 24 subagent
captures, 20 have it last, and 15 of those also carry the swallowed
`gitStatus:`, so 15 diverge. The defect is real and its blast radius today
is entirely in `log/prompt-captures/subagents/`.

It is latent for a second reason worth stating separately, because it will
not last: `survey_captures.py` globs the main directory only, so the wrong
flags are never printed. The bug is invisible because the only reader
happens not to read the affected rows -- which is `SILENT_DEFAULT` with an
accidental reprieve, not a mitigation.

**What would kill it.** A `# ` heading appearing after the scratchpad
section in subagent prompts upstream, which would fix the symptom without
touching the cause and would take the tripwire down with it.
