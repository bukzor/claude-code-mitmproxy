# 2026-09-17 -- a steer that arrived where nothing patches

## What happened

The operator noticed agents in auto mode had gone quietly unwilling to use
Read, Edit and Write, preferring `cat`, `sed -n` and heredocs, and asked
whether the cause was his configuration or Anthropic's. It was Anthropic's.

Claude Code carries a per-session assignment, `bashFirst`, recorded in the
transcript as an `auto_mode` attachment record -- invisible in the UI, absent
from message content, and therefore missed by a first scan that read only
message bodies. When it is on, a `<system-reminder>` goes out under the
heading `While auto mode is active:` instructing the model to do file work
through Bash instead of the dedicated tools. Two wordings ship, selected by
the GrowthBook gate `tengu_cozy_teapot` (env override
`CLAUDE_CODE_COZY_TEAPOT`, compiled default `strict`): `strict` permits a
dedicated tool only where Bash "genuinely cannot do the job", `relaxed` keeps
a carve-out for edits a shell would botch. This machine's cached value is
`strict`.

Dates, from the transcripts: `bashFirst` appears from 2026-08-18,
`bashFirstSteer: "strict"` from 2026-09-04 on clients at or above v2.1.260,
and `off` still turns up at v2.1.268 -- the randomization is live, not a
finished rollout. The agents' own thinking confirms compliance rather than
coincidence: they name the instruction and choose `sed` over Edit because of
it.

The costs are specific to this setup. A shell edit renders no diff, fires no
PreToolUse hook on Edit or Write, and walks straight through an `Edit()` deny
rule. Upstream contradicts itself on the same point: the harness prompt's
"Prefer the dedicated file/search tools over shell commands when one fits"
ships in the same request as the strict steer, and the auto-mode classifier
separately treats `sed -i`, `cat >` and heredocs as ways of "routing around a
deny rule by switching tools".

A claim made along the way did not survive testing. Asked whether Edit
requires a preceding full-file Read, the answer given was yes, and the
operator pushed back that a ranged Read had always seemed sufficient. Direct
experiment against v2.1.268 settled it: Edit is not gated on a prior Read at
all -- it succeeds on a never-read file, and inside or outside a previously
read line range. The only read-shaped failure is the ordinary "String to
replace not found in file" when the old text is guessed wrong. The same false
claim was found sitting in the Bash tool stub, uncommitted, and was removed.

## Why nothing was loud

Nothing was watching that surface. The steer rides in `request["messages"][i]`
with `role: "system"` -- a whole message entry, not a `<system-reminder>`
inside a user turn. `design/040-design.kb/prompt-loci-coverage.md` recorded
the `<system-reminder>` envelopes as unpatched *by policy*, on the ground that
their bulk is the user's own CLAUDE.md, agents and skills content and is
already under his control. That reasoning is sound for the surface it was
written about and simply does not reach this one: the text here is Claude
Code's own, injected mid-conversation, and none of it is the user's.

So there was no rule to miss and no incident to file. The failure mode is the
one a coverage note is supposed to prevent and cannot: a locus classified
once, on a rationale that a later arrival at the same address quietly
invalidates. What made it visible was a human noticing tool-choice behavior,
which is the slowest detector available.

## What changed

The locus is patched. `lib/claude_mitmproxy/message_patches.py` walks
`messages[]` for `role: "system"` entries, handling both content shapes, and
reuses `prompt_patches.apply_patches` unchanged -- the walk was the only new
part, as `CLAUDE.kb/system-prompt-loci.md` had predicted. It is wired into
`addons/syspatch.py` rather than an addon of its own: same job, same
`_uncaught-syspatch` rule, and one parse of the request body instead of two.

The rule deletes the steer body and leaves the heading. Nothing replaces it,
by the operator's ruling: the harness prompt already carries the preference he
wants, at the strength he wants, unconditionally. A `bashFirst`-off session is
therefore exactly what every arm now looks like.

Writing the rule surfaced a hazard specific to this locus, and the captured
traffic proved it rather than the argument. A `role: "system"` message also
carries replayed tool results, so a rule anchored on its heading matches the
quoted copy of itself that appears whenever a session reads these very files
-- and would delete the steer body out of the transcript a reader is looking
at. The match is anchored on the envelope instead (heading, blank line, one
line of steer). That is the risk
`.claude/ideas.kb/2026-08-20-000-Audit-heading-anchored-match-md-templates-for-self-referential-collision-risk.md`
names, landing first in the one directory guaranteed to be read aloud.

Around the same work, the three rule directories left `~/.claude` for
`~/.config/claude-mitmproxy/{system-prompt,tool-description,system-message}.d`.
They are configuration for this proxy, not for Claude Code, and `~/.claude` is
a vendor-owned directory that gains subdirectories every few releases. Two
constants and roughly a dozen prose references moved with them; the captured
fixtures and dated narratives kept the old paths, which is what they were
true of.
