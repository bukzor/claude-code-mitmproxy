---
cost-benefit-sweh:
  timebox:
    '@value': 1
    rationale: one code fix (incident dedup/skip); fast-mode verification demoted to ideas.kb 2026-07-05
    confidence: unsure
  benefit-2w:
    '@value': 0.3
    rationale: stops steady incident spam from auxiliary CLI requests; capture pipeline itself now verified live
    confidence: unsure
  cost-of-delay-2w:
    '@value': 0.2
    rationale: every CLI build bump re-captures the same auxiliary prompts, burying real drift signals
    confidence: unsure
---
# Todo

- [x] Stop `found-0-prompt-bodies` incident spam from auxiliary CLI requests
  (2026-07-05): added `cc_version=$CC_VERSION` masking to
  `incidents._VOLATILE_SUBS` — the billing header's build suffix was
  defeating `content_hash` dedup, re-capturing identical auxiliary prompts
  (session-title, web-search helper) once per CLI build. Verified against
  the 15 on-disk bodies: they collapse to 3 distinct shapes. Resolved
  incidents moved to `trash/resolved-incidents-2026-07-05/`. Note: the
  hash-scheme change orphans old digests, so each shape will re-capture
  once more on live traffic, then stay silent. Chose NOT to
  skip-and-not-capture auxiliary shapes: one capture per new shape is
  signal, spam was the only problem.
- [x] Verify patch-failure capture end-to-end live — the recorder path is
  proven: 13 real `found-0-prompt-bodies` incidents landed under
  `_locate-system-prompt/` + `_bodies/` from live `proxy.sh` traffic,
  2026-07-03..05.
  - [x] `logging.warning` flash in the mitmproxy status bar: user observed
    it working as intended (confirmed 2026-07-05).
- [x] Verify uncaught-exception capture end-to-end live — proven by real
  capture: thinkpatch's disabled-thinking `AssertionError` landed as
  `_uncaught-thinkpatch/4380a5b276ed` from live traffic 2026-07-04;
  root cause fixed in commit 42fe263, incident since trashed.
