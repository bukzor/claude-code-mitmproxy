# 2026-07-07: syscapture, v2.1.202/203 triage, and the design/ kb

Recovered on 2026-07-09 from the session transcript after the original
note was lost; kept because it is the origin record for two things the
repo now depends on. Names are as they were that day.

A repo survey turned into three lines of landed work:

- placeholder backreference semantics — same name means same text, with
  the `$LINES1`/`$LINES2` convention for when it must not;
- the `syscapture.py` addon, capturing the pristine pre-patch prompt
  body, which is what ended the contaminated-fixture pipeline;
- a `Skill(llm-design-kb)` why-chain under `design/`, plus
  `check_dark_patches.py` to sweep the silent-match-miss blind spot the
  loudness policy leaves open by design.

Also triaged the 2026-07-08 incidents: SDK-entrypoint title requests
exempted, v2.1.202/v2.1.203 fixtures promoted.

The one cross-session follow-up — verify that the parallel toolpatch
session's uncommitted work landed — is resolved: `toolpatch.py`,
`check_tool_patches.py`, and the `incidents.py` refactor are all in
`main`.
