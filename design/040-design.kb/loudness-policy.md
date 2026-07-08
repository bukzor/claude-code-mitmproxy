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

Shape exemptions are recognized by form (billing header, identity line,
task-prefix, `cc_is_subagent=true`), never by full text — so a drifted
interactive prompt still lands loud.

Because `match` misses are silent by design, they need a periodic
sweep: `check_dark_patches.py` prints the per-patch match matrix across
fixtures; run it whenever a new capture is promoted.

Triage procedure for the loud cases:
`../../CLAUDE.kb/patch-failure-triage.md`.
