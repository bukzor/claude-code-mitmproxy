# 2026-09-01 -- relitigating what the watch owes a reader

## What happened

The operator opened `/align` on the 2026-09-01 commits (2b8dfdd and a6b0238:
`--promote`, and promoting commits) with a suspicion: they accomplished the
goals as the agent understood them, and either the details violated an
implicit policy or the understanding fell short. The first pass came back as
a monologue with an "outcome" and was refused as such -- a relitigation is
two parties. What followed was a round of back-derived requirements (what
does a promotion still need to show a reader, and why), and a ruling on each.

## What was ruled

Promotion stays mechanical and commits, because "that's the usual case for
correct handling of the event. if that turns out to be false we should
revisit". What a reader still owes each fixture is a glance. The operator's
term for what the glance is for was flawed deduplication -- a fixture that
differs from a sibling only in text a rule should have neutralized -- and the
glance is a diff against the committed fixture with the smallest diff, found
exhaustively ("Can we get away with exhaustive diffing?"), with a tripwire on
the time it takes, because "the point of having a tripwire is our ignorance
of future scale, future refactoring". The watch runs `--promote` itself
("Yes that's my proposal"). The standing instruction reduces to one sentence,
address the Monitor output, so that "adjusting responsibilities amounts to
adjusting monitor output". Each line the watch prints carries a key into a
playbook, to "DRY the output (better token usage)" and so that
"documentation updates are decoupled from code". And the patch-failure
queue, which a reader had been told to triage whenever nonempty, becomes a
line the watch prints: "Is that not an 'event'? It may be just a matter of
changing its logging?"

## What changed

Filed over 2026-09-07. The rulings went into `design/040-design.kb/` first
(a0bf9a7). A fresh incident record is announced as an
`events.incident.<type>` event, typed off its rule name alone, and the gc
tool grew `--queue` to report the live queue as counts per rule (0334fd4).
`driftwatch.sh` runs the promotion pass and the queue report on every wake,
every line that asks something starts with its event type, and the pass
prints each fixture's diff against its nearest committed sibling and reports
itself over budget when the search exceeds `DIFF_BUDGET_SECONDS` (58e801c).
`playbook.kb/` holds one entry per type, held to the taxonomy by
`check_playbook` (cf671f1). The root `CLAUDE.md` standing duty became the
one sentence, as a vetoable draft.

Three agent choices along the way stand vetoable rather than ruled. Every
rule an uncaught exception is filed under now carries the `_uncaught-`
prefix so its type reads off the name, which makes the gc and compressor
failure records transients that expire unread. `--queue` lives on the gc
tool rather than as a new console script, because a new script needs a
`uv sync` and that waits for a proxy stop. And coverage is read from HEAD's
tree rather than the working tree, so a fixture a refused hook left on disk
covers nothing and is retried every pass.
