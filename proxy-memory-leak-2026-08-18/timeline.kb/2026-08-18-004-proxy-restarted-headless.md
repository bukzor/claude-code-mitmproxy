---
at: "2026-08-18T15:42:18-05:00"
source: startup log pasted by the user (timestamps from mitmdump's own event log)
confidence: observed
---

# Proxy restarted under the headless proxy.sh

New process: mitmdump, PID 19340. All six addons loaded, 18 system
prompt patches + 15 masks + 5 tool patches reported on stderr, clients
reconnected within a second. Baseline RSS ~97 MiB at +3 min
(`../evidence.kb/2026-08-18-009-baseline-rss-of-new-headless-mitmdump-process-pid-19340.md`);
no new patch-failure incidents. The TUI process and its half-GiB are
gone.
