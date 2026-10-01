---
managed-by: Skill(llm-subtask)
status: todo
---

# Unify pristine capture across loci

**Priority:** high for stage 1 -- the message locus has patching and no
pristine record, so "did upstream change, or did we delete it?" is currently
unanswerable after the fact; medium for the rest, which is architecture
**Complexity:** large -- five stages, each its own session; stage 1 is
independent of the other four
**Context:** proposed 2026-10-01. Design: `design/040-design.kb/one-walk-per-locus.md`.
Narrative: `session.kb/2026-10-01-the-gate-that-never-crosses-the-wire.md`.
This file is self-contained; neither is needed to start.

> [!DRAFT] agent-authored 2026-10-01, vetoable. The design entry's six open
> questions are unruled, and four of them change what gets built. The one thing
> already ruled is that the measurements below are not worth a long session's
> remaining context, so they are tasks here rather than findings there.

The prompt locus has a walk, pristine capture, promotion into
`system-prompts.kb/` and shape-keyed strip floors. The tool locus has a
hand-curated accepted set and an exact-compare tripwire. The message locus has
only the patch. Of the four pieces the prompt pipeline is built from, capture
is already locus-agnostic and the floors are already parameterized, so the
work is wiring them to a declaration rather than writing them again.

## Stage 1: the message locus, standalone

Independent of every other stage, and the only one that closes a live gap.
Routing novelty through the incident queue rather than the promotion pass is
what decouples it -- see the design entry on occasion-driven loci.

- [ ] Measure the session-breadth discriminator against the logs on disk: for
      each masked digest of a `role: "system"` body, how many distinct
      `X-Claude-Code-Session-Id` values carry it. Confirm Claude Code's own
      bulletins separate from replayed session content.
- [ ] Measure distinct bodies per day at this locus after recognition. The
      volume question is about distinct masked digests, not occurrences: one
      file read is one body however many requests replay it.
- [ ] Measure the surviving shape vocabulary. A small stable set makes kb
      promotion cheap and answers the design entry's last open question.
- [ ] Extend `masks.d/` for the paths, dates and line numbers these bodies
      carry, and prove dedup stable across a day of real traffic. Without
      this, every new path files a fresh novelty report.
- [ ] Add the capture walk to `addons/syscapture.py`, which loads before every
      patch addon and therefore sees pristine text. The patch walk stays in
      `addons/syspatch.py`.
- [ ] Capture to `log/message-captures/`, dedup by masked digest, write once.
- [ ] File a never-before-seen body to the queue under
      `_novel-system-message`, with its `playbook.kb/` entry --
      `check_playbook` holds the two in correspondence.

### Measured 2026-10-01, partial answers to the third task above

From `log/traffic/` on disk. Read with one caveat: `flow2jsonl` loads after
`syspatch`, so these records are what was sent upstream, not pristine. For
first-line vocabulary that is immaterial -- the only rule at this locus
deletes a body line and leaves its heading -- but it is the reason stage 1
exists, and a measurement taken here cannot stand in for one taken at capture.

Normalizing paths, dates, uuids, long digit runs and tool-argument JSON out of
the first line of each `role: "system"` body, the distinct first lines number
8 on 2026-10-01, 9 on 2026-08-17 and 13 on 2026-08-18. The vocabulary is small
and stable, which is what makes kb promotion cheap. Splitting the same bodies
on blank lines instead yields 158 distinct section openers in a single day,
nearly all of it the heading structure of documents a session happened to
read -- a measure of what the recognition predicate has to separate out, not
of the vocabulary.

The one arrival with a known date was detectable the day it happened.
2026-08-18 is the day the bash-first steer first shipped, and that day's first
lines went 9 to 13 against 2026-08-17: five new strings, one of them
`While auto mode is active:`. The operator found it on 2026-09-17 by noticing
tool-choice behavior. So novelty reporting at this locus is worth about thirty
days of latency against the slowest detector available, measured rather than
argued.

Also measured, and the standing reason stage 1 is worth doing beyond
forensics: four upstream instructions ride this locus today that no one has
ever ruled on. They are listed in `.claude/todo.md` as their own review task.

## Stage 2: four roles in one patch dialect

- [ ] Add the `expect` role to `rule_templates.py` and implement the default
      chain: write region is `search`, `search` defaults to `match`, `match`
      defaults to the whole body, `expect` defaults to `search`.
- [ ] Replace the load-time "match required" assert with "at least one of
      match, search, expect", preserving the half-created-directory guard.
- [ ] Validate against the whole rule corpus by rendering before and after and
      diffing, not by the test suite alone.
- [ ] Amend the `match`/`search` paragraph in
      `design/040-design.kb/template-patch-model.md`, which the four roles
      supersede.

## Stage 3: merge the two patch engines

- [ ] Express each tool stub as a dialect rule: `expect.d/` plus `replace.md`,
      naming neither `match` nor `search`.
- [ ] Delete `tool_patches.py` and `check_tool_patches.py`.
- [ ] Retire `changed-upstream` in favor of the generic expect-miss, and
      update `playbook.kb/` accordingly.

## Stage 4: the locus table

- [ ] Add the locus record: a name, a walk, and the walk's traversal data.
- [ ] Derive `~/.config/claude-mitmproxy/{name}.d` and `{repo}/{name}s.kb`
      from the name; delete the duplicated `KB_DIR` constants in
      `prompt_patches.py` and `survey_captures.py`, one of which is
      cwd-relative and the other repo-root-relative.
- [ ] Migrate the system-prompt and subagent-prompt loci unchanged, proving
      behavior identical before any new locus joins the table.
- [ ] Assert that the capture addon loads before every patch addon.
      `addons/reload.py` asserts imports, not order, and three loci will
      depend on that order rather than one.
- [ ] Generate `design/040-design.kb/prompt-loci-coverage.md` from the table.

## Stage 5: shape keys and the tool migration

- [ ] Persist the shape key in capture filenames, filename-safe, with
      "unrecognized" still representable.
- [ ] Move `prompt_shape` inside the prompt walk; delete `FIXTURE_SUFFIX` and
      its correspondence assert, which the shapes-equal-suffixes rename makes
      redundant.
- [ ] Migrate the tool locus last: `tool-description.d/*/upstream.d/` in the
      personal repo becomes `tool-descriptions.kb/` in this one, per the
      authority split.
