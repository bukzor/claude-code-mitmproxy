---
managed-by: Skill(llm-subtask)
---

# Todo

Use subtasks, not sections for organization. Ordered by intended completion.
Narrative in `../session.kb/`.

- [x] `apply_patches` appends a trailing newline even when no patch
      applies — unpatched bodies differ from stock by one byte. First
      because it puts a `+1` on every `check_patches.py` delta, which is
      exactly the measurement the work below depends on reading correctly
- [x] Guard against the silent-empty patch set: `load_patches` returns `()`
      when its `~`-relative dir is missing, so a wrong `$HOME` measures as a
      clean zero-strip run rather than failing. An empty patch set is never
      legitimate here — assert. Same for `load_tool_patches`
- [ ] Re-establish ground truth after the v2.1.221 prompt rewrite —
      blocks every patch item below
  - [x] Identify the 27k `claude-sonnet-5` captures: the **old** shape,
        still served at v2.1.221, plus a ~130-line session-optional
        `# auto memory` block. The rewrite is model-scoped (opus-5/fable-5
        new, sonnet-5 old), not version-wide
  - [x] Run `check_patches.py` against every v2.1.221 shape; record which
        patches match where — matrix in `session.kb/`
  - [ ] Promote the v2.1.221 captures into `system-prompts.kb/` per the
        pattern in git log — now needs all three model shapes, not just
        long-form + `-harness`; record the naming in
        `system-prompts.kb/CLAUDE.md`
  - [ ] Run `check_dark_patches.py` against every promoted shape
- [ ] Repair the two patches that still have a live target and miss it —
      the only items here that restore stripping rather than bookkeeping
  - [ ] `strip-git-status`: add `match.d/v2.1.221.md` — live block has a
        blank line after `gitStatus: $REST` (unlike v2.1.76) and no
        `Git user:` line (unlike v2.1.128), so both variants miss
  - [ ] `strip-fast-mode-info`: retarget from the `<fast_mode_info>` tag
        to the unconditional `# Environment` bullet ("Fast mode for Claude
        Code uses Claude Opus with faster output (it does not downgrade to a
        smaller model). It can be toggled with /fast and is available on
        Opus 5/4.8."), and clear the UNVERIFIED caveat in its README
- [ ] Sunset the patches whose target text is gone upstream — each gets
      `upstream-removed.bool: true` and loses `replace.md`/`search*`, one
      commit apiece. Before the new patches, so the tree stops lying about
      what it strips. Scope is narrow: the old shape is still served to
      sonnet-5, so only patches that match *no* live shape qualify
  - [ ] `strip-tool-preference` (`# Using your tools`) — matches no shape
  - [ ] `strip-output-efficiency` (`# Text output`) — matches no shape
  - [ ] `strip-additional-dirs` — matches only the promoted v2.1.214
        capture, no live shape; decide sunset vs. retarget before acting
- [ ] Add patches for the v2.1.221 shape — mechanical ones first, the
      two rewrites last since they are opinion rather than drift
  - [ ] `strip-duplicate-parallel-tools`: the parallel-tool-call
        directive appears in `# Harness` and again as the closing line;
        strip the second
  - [ ] `strip-agent-types-listing`: the injected agent-types block
        contradicts the standing `Do not call the AgentTool unless the user
requested it` line — strip one, decide which
  - [ ] `strip-scratchpad-bloat`: `# Scratchpad Directory` spends five
        bullets and an all-caps IMPORTANT on a one-sentence rule
  - [ ] `condense-delivering-work`: ~450 words restating "do what was
        asked, don't rescope, finish it, flag concerns once" five or six ways
  - [ ] `condense-corrections`: ~250 words restating "correct errors that
        matter, don't ruminate" seven ways
- [ ] Extend `~/.claude/tool-description-patches.d/` past its two patches
      (`Monitor`, `SendMessage`), neither served to opus-5 in the new shape
  - [ ] Triage `log/patch-failures/tooldesc-Monitor`
  - [ ] `EndConversation` stub: largest description served, and the
        never-taken path; carries a full policy plus a subsection on
        background forks calling it
  - [ ] `Bash` trim: the git-convention block (commit trailers, PR body
        footer, `gh` usage) loads every session including non-git ones
  - [ ] `Agent` trim: fork/worktree/remote semantics load even when the
        standing instruction forbids calling it
- [ ] Consider an aggregate-strip-rate check that fires when the total
      falls far below a recorded baseline — no per-patch rule can see a
      whole-document rewrite, since every individual miss is legitimately
      silent. After the patches, so the baseline it records is a real one
- [ ] Documentation debt from the rewrite — last, so it describes the
      finished state
  - [ ] `system-prompt-patches.d/README.md`: the "~32% of the long-form
        (15.0k → 10.2k)" stats are v2.1.199-era; restate against v2.1.221
  - [ ] `system-prompts.kb/CLAUDE.md`: record the long-form/`# Harness`
        convergence — the two-shape model that the README's `search.d/`
        guidance assumes may no longer hold
  - [ ] `CLAUDE.md`: `session.kb/` is a new top-level collection and is
        not in the Collections list; add it or fold it into an existing one
- [ ] Decide `system.patched.md`'s fate: tracked but v2.1.76-era stale;
      regenerable, so delete (with matching `NOTICE`/README license edits) or
      regenerate with a stated purpose
- [ ] Decide `jsonl2sysprompt.sh`'s fate: its kb-capture job moved to
      `syscapture.py` (and its output is post-patch contaminated); keep as a
      jsonl-archaeology utility, or delete it and its README entry.
- [ ] Remaining trivia from 2026-07-12 review
  - [ ] `flow2jsonl.sh` uses `tail -f` (never exits at EOF); README says
        "replay" — fix whichever is wrong
  - [ ] syspatch README testing example references defunct `system.md`
        naming
