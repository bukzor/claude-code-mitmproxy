---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.5
    rationale: |
      The seed script already exists and passes; the exploration is just
      deciding where it lives (tests/ + runner) and what env runs it.
  benefit-2w:
    "@value": 1.0
    rationale: |
      request() is now nontrivial (locator + capture + pass-through) and
      check_patches.py only exercises apply_patches; regressions in the
      addon hook are currently only caught live.
---

# Addon-level request tests via mitmproxy.test

## The Idea

Keep permanent tests for `syspatch.request()` — the mitmproxy addon hook —
driven by fake flows built with `mitmproxy.test.tflow`/`tutils.treq`. The
offline validator (`check_patches.py`) covers `apply_patches` only; the
hook's own logic (system-shape dispatch, prompt-body locator, incident
capture, pass-through) has no repeatable check.

Working seeds exist: `trash/test_locator.py` (2026-07-03: found-0
capture + pass-through, dedup on repeat, happy one-body path) and
`trash/test_syscapture.py` (2026-07-08: fresh capture, masked-digest
dedup, non-interactive pass-through, string-system fallback).

## Potential Benefits

- Regressions in `request()` caught offline instead of as live Addon errors.
- Cheap to extend when new loci are patched (see
  `CLAUDE.kb/system-prompt-loci.md` — tools[].description, system-reminder
  envelopes).

## Open Questions / Unknowns

- Test runner/env: the repo has no pytest setup; tests need the uv-tool
  mitmproxy interpreter (`~/.local/share/uv/tools/mitmproxy/bin/python`) or
  a proper dev venv.
- Whether `thinkpatch.py` should get the same treatment.
- 2026-07-04: `incidents.py` now also captures uncaught exceptions from all
  three addons' hooks (`_uncaught-{addon}` rule, see
  `CLAUDE.kb/patch-failure-triage.md`). Verified only by an ad hoc scratch
  script (not committed) that exercised `syspatch.request()`,
  `thinkpatch.request()`, and `flow2jsonl.request()`/`response()` against
  malformed/error-inducing flows. No permanent regression test exists for
  `capture_uncaught` or the wrapping — same gap this idea already names,
  now with one more addon-level behavior to cover whenever it's promoted.
- 2026-07-09: `incidents.py` gained `archive_incident`/`_body_still_live`
  (moves a resolved incident to `log/patch-failures/_archive/`, keeping a
  shared body live until no other rule still references its digest) and
  `gc_patch_failures.py` gained `gc()` (age-prunes `_archive/` by mtime).
  Both verified only by an ad hoc scratch script (not committed) covering
  the shared-body case and dry-run vs. real deletion — same gap, same
  shape.

## Next Steps (if pursuing)

- [ ] Promote `trash/test_locator.py` into `tests/` with a documented runner
- [ ] Convert asserts to pytest cases; add a found-2 case

## Lifecycle

**Status:** Exploring
