---
managed-by: "Skill(llm-subtask)"
status: open
required-reading:
    - ../root-cause.kb/console-flow-store-retention.md
cost-benefit-sweh:
    timebox: 1
    benefit-2w:
        "@value": 1
        rationale: >-
            An unattended OOM kill of the proxy mid-session would cost
            an hour of confused recovery across every live Claude Code
            session; a bound prevents recurrence.
---

# Confirm store retention, then adopt a memory bound

1. ~~Run the `view.clear` test~~ done 2026-08-18 15:09: quiet outcome,
   ~20 MiB returned (`../findings.kb/view-clear-returned-little-to-os.md`).
2. ~~Adopt a bound~~ done via `../remediations.kb/run-headless-mitmdump.md`
   (proxy.sh execs mitmdump; store-cap addon rejected as superseded).
3. ~~Restart the proxy~~ done 2026-08-18 15:42 by the user: mitmdump
   PID 19340, baseline ~97 MiB, no new incidents.
4. ~~Confirm the root cause~~ done 2026-08-18 15:25: post-clear plateau
   under traffic (`../findings.kb/post-clear-rss-plateau-under-traffic.md`);
   `../root-cause.md` rewritten as the answer. ~~After a day of traffic
   under mitmdump, capture RSS once more as fix verification~~ done
   2026-08-21: 99 MiB -> 141 MiB over ~66.6 h, ~30x slower than the
   pre-fix leak rate (`../findings.kb/headless-mitmdump-growth-rate-is-normal.md`).
5. The host still has no proxy-RSS monitoring
   (`../environment.kb/host-and-proxy.md`) -- decide whether this
   incident warrants one before closing. OPEN QUESTION for the user: the
   day-3 read still shows slow monotonic growth (no plateau/shrink), just
   far slower than the leak -- close as "normal, no monitoring" or keep
   watching a while longer / add a cheap periodic RSS log before closing?
