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

What survives both routes has to arrive on its own. Two channels do that, and
which one a signal takes follows from how durable its evidence is.

A patch miss or a tool-description drift holds *transient* evidence -- the body
that failed to match, as it was at that moment -- which is gone if nothing
stores it. Those go through the incident store, where [earned-silence] already
governs them: one warning per distinct content, deduped on disk, triaged by the
one procedure.

Fixture promotion is the other kind. Nothing is loud when upstream ships prompt
text no fixture covers, because additive drift trips no tripwire
([fixture-lifecycle]) -- but the fact is a pure function of on-disk state
(`log/prompt-captures/`, `system-prompts.kb/`, `blocks.d/`) and recomputable
whenever asked. A record of it would cache a derived value, which
`prompt_capture` declines to do on the same grounds. So what drift needs is not
durable emission but *timely* emission, and the incident queue cannot supply
that: a nonempty queue is itself something someone has to notice, so routing
drift there would consolidate two polls rather than retire either. It is polled
by `driftwatch.sh` instead and arrives as a notification in a maintenance
session.

> [!DECISION] an uncovered core at the newest release on disk gets the warning
> Agent-ratified and vetoable -- asked to choose, the operator had no
> preference, so a session chose; the notification channel is the operator's
> counter-proposal.

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

`driftwatch.sh` waits on inotify across the predicate's three inputs and
re-evaluates when any changes -- `system-prompts.kb/` and `blocks.d/` included,
since promoting a fixture is what clears a standing report and watching only
the captures would hold it red until some unrelated capture arrived.

Two questions live here and are easy to fuse: what *wakes* the loop, and what
decides to *notify*. A capture event really is a superset of a drift event, but
that argues only against notifying on the event. With the predicate still
filtering, waking on a capture that turns out to be covered costs one
evaluation and says nothing. Polling instead costs about a second of CPU per
evaluation, so any interval short enough to feel responsive buys a duty cycle
paid for the life of the session -- to re-derive an answer whose inputs are
usually untouched.

A ceiling on the wait is what keeps that honest. A change landing between an
evaluation and the next wait would otherwise sit undetected, and a watch that
quietly stopped working would be indistinguishable from no drift. When the
watcher cannot run at all the loop sleeps instead, degrading to a slow poll
rather than spinning or dying.

What this route does *not* deliver, stated rather than smuggled: the signal is
only as live as the session that armed it. Coverage is "within a minute while a
maintenance window is open, and on the first pass of the next one", which is
enough because promotion has no deadline tighter than the next time a check's
silence has to mean something. Arming the watch is therefore setup bound to
session start, not a duty -- it asks nothing when nothing happened -- but the
binding is an instruction rather than a hook, because `Monitor` is an agent
tool and a hook cannot call one.

## What stays a duty

Triage. Reading a captured body and deciding whether upstream reworded, moved
or retired a patch's target is judgment about someone else's prose, and no
occasion produces the answer. Leaving that as the only standing obligation is
the point of the three routes above, not a gap in them.

[compression-at-shard-open]: ease-of-operation.kb/compression-at-shard-open.md
[earned-silence]: ../020-goals.kb/earned-silence.md
[fixture-lifecycle]: fixture-lifecycle.md
