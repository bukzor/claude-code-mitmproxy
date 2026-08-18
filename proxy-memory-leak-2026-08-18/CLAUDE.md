--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-kb)
    - Skill(incident-forensics)
---

# Proxy memory leak (2026-08-18) -- Investigation kb

The long-lived mitmproxy reverse proxy in front of api.anthropic.com
(PID 31950, the interactive TUI launched by `proxy.sh`, started
2026-08-17 ~10:57 -05:00) reached ~526 MiB RSS after ~28 h -- at its
all-time peak (VmHWM == VmRSS, i.e. monotonic growth) and still creeping
upward under live traffic. No OOM, no fd/thread leak; the host still had
~3.4 GiB available. Root cause confirmed same day (`root-cause.md`): the
TUI's view store retains every flow with no eviction, times Claude
Code's very large request bodies. Fixed by switching `proxy.sh` to
headless mitmdump (restarted 15:42, baseline ~97 MiB); day-after RSS
check remains as fix verification (`todo.kb/`).

Collections, one per information type:

- `timeline.kb/` -- dated events of the incident; `timeline.md` synthesizes
- `evidence.kb/` -- raw captures; append-only, never rewritten
- `findings.kb/` -- conclusions distilled from evidence, status-tracked
- `root-cause.kb/` -- candidate explanations; `root-cause.md` is the decision point
- `environment.kb/` -- static machine context (topology, resources, monitoring)
- `remediations.kb/` -- prevention/recovery measures and adoption status
- `reports.kb/` -- outbound upstream contributions and posting status
- `todo.kb/` -- next actions, Skill(llm-subtask) conventions

Maintenance:

- New evidence lands as a new dated file in `evidence.kb/`; then update the
  `status`/`evidence` of affected findings and root-cause candidates --
  never edit a capture to match a conclusion.
- When the root cause closes, rewrite `root-cause.md` to state the answer;
  keep `root-cause.kb/` as the record of why alternatives lost.
- Update `last-updated` in `README.md`/`timeline.md` when their content changes.
