---
why:
  - ../020-goals.kb/earned-silence.md
---

# Loudness policy

Every non-application is classified; the class decides the band:

| Event | Response | Why |
| --- | --- | --- |
| `match` miss | silent | self-scoping: the patch detected it doesn't apply here |
| `search` miss after `match` hit | incident, warn once | in-scope target vanished: real drift |
| `upstream-removed` patch matches | incident, warn once | sunset text returned upstream |
| tool description off-fixture | incident, warn once | the stub may now hide new upstream guidance |
| no prompt body, recognized shape (aux/subagent) | `debug` log | expected on every Task-tool call |
| no prompt body, unrecognized shape | incident, warn once | new request shape, or drifted body marker |
| patched body strips less than its shape's floor | incident, warn once | the one miss no per-patch rule sees: every shape-scoped patch out of scope at once |
| digest mask matches nothing | silent | masks run over tracebacks and subagent bodies too; finding nothing is the norm |

Shape exemptions are recognized by form (billing header, identity line,
task-prefix, `cc_is_subagent=true`), never by full text — so a drifted
interactive prompt still lands loud.

Because `match` misses are silent by design, they need a sweep --
periodic in the sense that promotion is periodic, not that anyone
schedules it (`every-duty-has-an-occasion.md`).
`check_dark_patches.py` prints the per-patch match matrix across
fixtures, and the commit that promotes a capture runs it. A mask, whose
misses are silent unconditionally, gets the stronger form of the same
sweep — `check_masks.py` *fails* on a mask no fixture exercises, since
unlike a patch there is no legitimate reason for a mask to be dark
across the whole fixture set. The `check_dark_patches.py` sweep also
flags SUBSUMPTION: a patch whose `match` hits the raw fixture but no
longer hits once earlier patches (load order) have already run against
it, in which case it's silently dead in the real pipeline even though a
raw-only check would call it live (e.g. `strip-help-feedback` anchored
its `match` on the same `# Doing tasks` heading that
`strip-doing-tasks-bloat` deletes wholesale — always subsumed, fixed
2026-07-13 by matching its own target text directly).

The floor in that last row needs its own sweep, because a threshold set
too high is indistinguishable in production from the drift it exists to
catch. `check_strip_floors.py` asserts that no capture on disk strips
less than its shape's floor: a floor above ordinary traffic makes every
sparse session loud, which is precisely the noise `earned-silence`
forbids. It is calibrated on fixture *cores* for that reason
(`fixture-lifecycle.md`).

## The same warrant applies to an `except` clause

A handler either re-raises or **handles** -- and handling means producing the
answer the failure implies, as distinct from doing nothing. `continue` and
`pass` are where this hides, since both read as control flow while being
neither: the silence is unclassified, which is what `earned-silence` forbids
one rung down, in code.

The repair is usually to convert the exception into the value it means, at the
point it is raised, so the handler returns an answer instead of resuming:
`flocked_logs.holds_lock` asks whether an fd holds the lock by trying to take
it, and `fd_target` answers "what does this fd point at" with None once the fd
is gone. What survives the conversion is a handler with a warrant, and the
warrant belongs on the line beside it -- `flow2jsonl._default` passes on a
`BadGzipFile` because bytes that were never gzipped are already the answer.

Catch the class that was argued for, not its superclass. `fd_target` catches
`FileNotFoundError` rather than `OSError` because its callers reason from an
exhaustive view of our own fds: a permission error absorbed there would leave
that reasoning intact and wrong.

Triage procedure for the loud cases:
`../../CLAUDE.kb/patch-failure-triage.md`.
