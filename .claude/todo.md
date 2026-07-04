---
cost-benefit-sweh:
  timebox:
    '@value': 2
    rationale: two live-verification items; the triage item is blocked on the next found-0-prompt-bodies occurrence
    confidence: unsure
  benefit-2w:
    '@value': 0.3
    rationale: confidence in the capture pipeline; the patch itself is already hot-fixed
    confidence: unsure
  cost-of-delay-2w:
    '@value': 0.1
    rationale: the blocked item self-serves as verification when it fires
    confidence: unsure
---
# Todo

- [ ] Triage the live `found-0-prompt-bodies` incident once a capture lands
  under `patch-failures/_locate-system-prompt/` (blocked on the next
  occurrence; the addon hot-reloaded the 2026-07-03 fix, commit 77815a8).
  Read `_bodies/{digest}.md`, decide: `BODY_MARKER` drifted (add marker
  alternatives) vs. a non-Claude-Code request shape (leave unpatched by
  design). See `CLAUDE.kb/patch-failure-triage.md`. When it lands it also
  serves as the live end-to-end capture verification the next item wants.
- [ ] Verify patch-failure capture end-to-end live: run `proxy.sh`, route Claude
  Code through it, induce a patch miss (e.g. stale `match.md`); confirm the
  `logging.warning` flashes in the mitmproxy status bar and the records land
  under `patch-failures/_bodies/{digest}.md` + `patch-failures/{rule}/{digest}.json`.
  (Curses behavior is so far asserted from mitmproxy 12.2.1 source, not
  observed. The content-addressed/dedup recorder was reworked 2026-06-23 and
  tested offline only — live capture still unverified.)
- [ ] Verify `strip-fast-mode-info`'s `match.md` against a real capture with
  `/fast` toggled on. It targets a `<fast_mode_info>` tag reading "uses the
  same Claude Opus 4.6 model" but the *unconditional* Fast Mode line
  elsewhere in the current prompt already says "Opus 4.8/4.7" — same
  stale-version smell `strip-over-engineering` had before it was found to be
  silently dark. See `~/.claude/system-prompt-patches.d/strip-fast-mode-info/README.md`.
  Toggle `/fast` in a proxied session, capture via `traffic.jsonl`,
  compare the tag's current wording, re-target `match.md`/add `search.md` if
  it drifted.
