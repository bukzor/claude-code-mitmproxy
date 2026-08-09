---
why:
  - earned-silence
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
| digest mask matches nothing | silent | masks run over tracebacks and subagent bodies too; finding nothing is the norm |

Shape exemptions are recognized by form (billing header, identity line,
task-prefix, `cc_is_subagent=true`), never by full text — so a drifted
interactive prompt still lands loud.

Because `match` misses are silent by design, they need a periodic
sweep: `check_dark_patches.py` prints the per-patch match matrix across
fixtures; run it whenever a new capture is promoted. A mask, whose
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

Triage procedure for the loud cases:
`../../CLAUDE.kb/patch-failure-triage.md`.
