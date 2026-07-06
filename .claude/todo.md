---
cost-benefit-sweh:
  timebox:
    '@value': 1.5
    rationale: one code fix (incident dedup/skip), one narrowed live observation, one match.md re-verification
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

- [ ] Stop `found-0-prompt-bodies` incident spam from auxiliary CLI requests.
  Triage 2026-07-05 found all 13 captures are non-interactive request shapes
  (session-title generation, web-search helper, bare "You are Claude Code"
  header) — unpatched by design, not marker drift. But dedup is broken:
  the `x-anthropic-billing-header` block embeds the cc_version *build
  suffix* (`2.1.201.f67` vs `.761` vs `2.1.200.48f`...), so `content_hash`
  treats the identical session-title prompt as a new incident per CLI
  build. Fix in `incidents.content_hash` neutralization (mask the
  cc_version value) and/or teach the `_locate-system-prompt` check to
  skip-and-not-capture recognized auxiliary shapes. Then delete the 13
  resolved incidents (verdict recorded here; bodies are boilerplate,
  no kb capture needed).
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
- [ ] Verify `strip-fast-mode-info`'s `match.md` against a real capture with
  `/fast` toggled on. It targets a `<fast_mode_info>` tag reading "uses the
  same Claude Opus 4.6 model" but the *unconditional* Fast Mode line
  elsewhere in the current prompt already says "Opus 4.8/4.7" — same
  stale-version smell `strip-over-engineering` had before it was found to be
  silently dark. See `~/.claude/system-prompt-patches.d/strip-fast-mode-info/README.md`.
  Toggle `/fast` in a proxied session, capture via `traffic.jsonl`,
  compare the tag's current wording, re-target `match.md`/add `search.md` if
  it drifted.
