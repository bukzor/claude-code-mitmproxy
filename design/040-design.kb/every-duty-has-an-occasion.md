---
why:
  - ../020-goals.kb/earned-attention.md
---

# Every duty has an occasion

Three routes retire a recurring obligation, ordered by what they cost the
operator. Take the earliest one that applies.

## Argue it away

A duty can be deleted outright when nothing is lost by never performing it.

Uncaught-exception incidents are the case. A live-edit transient -- a mid-refactor
save the proxy re-executed -- and a standing bug in an addon hook are
indistinguishable at capture time, and are told apart only by waiting. So
`gc_patch_failures` waits, and archives `_uncaught-*` records unread once they
pass the retention window.

What licenses that is a property the store already had:
`incidents.save_incident` is idempotent per (rule, content), so removing a
record restores the warning. A cause that is still live re-files on its very
next request; a transient never returns. Guessing "spent" wrong therefore
costs one delayed warning rather than a lost one.

The argument is also the limit. It covers `_uncaught-*` and nothing else: for
a patch miss or a tool-description drift, the record's age is evidence of
neglect rather than of resolution, and expiring one would delete the only
notice that upstream moved.

## Bind it to its occasion

Where the work must really happen, it happens at the event that creates it,
never on a clock and never in a checklist.

| Duty | Occasion |
| --- | --- |
| reclaim spent incidents and archives | proxy start (`gc_patch_failures.sweep_at_startup`, from `addons/syspatch.py`'s load hook) |
| validate masks, blocks and fixtures | the commit that touches `masks.d/`, `blocks.d/` or `system-prompts.kb/` (`.pre-commit-config.yaml`) |
| compress finished traffic shards | opening a shard ([compression-at-shard-open]) |

The check case is the cleanest fit, because the occasion is not merely
convenient: those three directories are the entire input to every `check_*`
module, so a commit touching one is both the only thing that can change a
verdict and the moment someone is changing it.

An occasion is usable only when it recurs faster than the duty's window and
cannot be skipped while the work continues. Proxy start qualifies against a
30-day retention window; it would not against a daily one, and a duty with no
such occasion has to take the third route instead.

Housekeeping bound this way reports failures rather than raising them: a
sweep that cannot run files a `_gc-patch-failures` incident, because a proxy
that patches traffic with a cluttered `log/` is better than one that refused
to start over disk hygiene.

## Make it loud

What survives both routes goes through the incident store, where
[earned-silence] already governs it -- one warning per distinct content,
deduped on disk, triaged by the one procedure.

Fixture promotion is what survives them. Nothing is loud when upstream ships
prompt text no fixture covers, because additive drift trips no tripwire
([fixture-lifecycle]); `survey_captures.py --drift` computes the answer but
must be run by someone.

> [!DECISION] an uncovered core at the newest release on disk gets the warning
> Agent-ratified and vetoable -- asked to choose, the operator had no
> preference, so a session chose. Decided, not built: CLAUDE.md carries
> promotion as a duty until it is.

Compare `Capture.sort_key`'s numeric triple only. Excluding the build tag is
load-bearing rather than pedantic: tags are hashes, so order between them is
noise, and on 2026-08-29 the newest tag (`2.1.251.da4`) carried no uncovered
core while its release carried two -- compared whole, the predicate goes silent
on exactly the drift it exists to catch. So compared, it restates the duty
rather than approximating it, and it clears itself: promoting the named raws
quiets it until the next release. A one-off capture at a current release fires
it too, and triage ends that one by archiving, so `seen` belongs in the message
to keep that call cheap.

Two alternatives were weighed and withdrawn. **Recurrence** -- an uncovered
core seen in two or more captures -- measures how long a copy survived the
backlog rather than whether upstream serves it: it fires on seven copies today,
none newer than 2.1.250.257, and says nothing about either 2.1.251 copy. **A
continuous drift score**, PID-shaped (uncovered count, its sum over a recent
window, its rate of change) and thresholded into the same warning, fails
differently. Drift's cost is categorical rather than proportional -- one
uncovered copy of what is served now is the whole problem, and eighteen copies
of what nobody serves is none of it -- so a sum over copies has units nothing
cares about. The integral also cannot fire in time: upstream ships a build most
days, and a copy's entire service life can hold one capture (`cb735fcae57c` was
served at 2.1.251.171, captured once, superseded within its own release), so
any threshold above one capture is silent by construction on the copies that
matter, while a threshold of one is the predicate again. And a score cannot
carry its own remedy -- this alarm exists to hand over a raw path to promote,
which a row does and a number cannot. What survives is the derivative
intuition, and the predicate is already it: a step detector on release
identity rather than on a count.

## What stays a duty

Triage. Reading a captured body and deciding whether upstream reworded, moved
or retired a patch's target is judgment about someone else's prose, and no
occasion produces the answer. Leaving that as the only standing obligation is
the point of the three routes above, not a gap in them.

[compression-at-shard-open]: ease-of-operation.kb/compression-at-shard-open.md
[earned-silence]: ../020-goals.kb/earned-silence.md
[fixture-lifecycle]: fixture-lifecycle.md
