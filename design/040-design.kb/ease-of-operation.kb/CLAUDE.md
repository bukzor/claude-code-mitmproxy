# ease-of-operation.kb — operational-continuity design entries

Belongs here: invariants about keeping the proxy runnable unattended
long-term -- output growth, restart safety, anything that bites only
after days of uptime rather than on the next request.

Does not belong: patch-application behavior or capture semantics that
hold regardless of uptime (parent `040-design.kb/`); goal-level framing
(`../../020-goals.kb/ease-of-operation.md`).

When to add: a new failure mode specific to long-running or
frequently-restarted operation is found and fixed.
