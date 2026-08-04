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
- [x] Re-establish ground truth after the v2.1.221 prompt rewrite —
      blocks every patch item below
  - [x] Identify the 27k `claude-sonnet-5` captures: the **old** shape,
        still served at v2.1.221, plus a ~130-line session-optional
        `# auto memory` block. The rewrite is model-scoped (opus-5/fable-5
        new, sonnet-5 old), not version-wide
  - [x] Run `check_patches.py` against every v2.1.221 shape; record which
        patches match where — matrix in `session.kb/`
  - [x] Promote the v2.1.221 captures into `system-prompts.kb/` —
        `v2.1.221.md` (sonnet long-form) + `-opus`/`-fable` model-scoped
        variants (opus and fable turn out to be *different* new shapes);
        naming recorded in `system-prompts.kb/CLAUDE.md`
  - [x] Run `check_dark_patches.py` against every promoted shape —
        warnings unchanged from baseline (the 2 known-explained v2.1.128)
- [x] Repair the two patches that still have a live target and miss it
  - [x] `strip-git-status`: added `match.d/v2.1.221.md` (dotfiles@4d06228)
        for the opus-5 shape. Correction to the premise: only opus missed —
        the fable block is v2.1.128-shaped (has `Git user:`) and was being
        stripped all along; its matrix "miss" was a `check_dark_patches.py`
        false negative (no trailing-newline normalization, fixed @576dbd5)
  - [x] `strip-fast-mode-info`: retargeted to the `# Environment` bullet
        (dotfiles@0c9b06c) — match on the heading, `search.d/` variants for
        the bullet (version tail as `$REST`) and the old v2.1.76 tag;
        README caveat cleared, verified against all promoted fixtures
- [x] Sunset the patches whose target text is gone upstream — resolved
      with zero commits: nothing qualified
  - [x] `strip-tool-preference` — already sunset (committed
        `upstream-removed.bool`, conformant layout); item was stale
  - [x] `strip-output-efficiency` — same, already sunset
  - [x] `strip-additional-dirs` — has a live target after all: the fuller
        `b87` fable capture carries the additional-dirs block and the patch
        HITs it (the matrix session's capture just lacked the optional
        block). Keep unchanged
- [ ] Classify the v2.1.221 haiku capture — a fourth live shape
      (`# User's Current Configuration`, 22k, has gitStatus + scratchpad)
      that no patch consideration covers; main-loop or auxiliary? Promote
      it or teach `syscapture.py` to file it as auxiliary
- [ ] Triage `~/.claude/system-prompt-patches.d/strip-help-feedback`'s
      uncommitted 2026-07-13 change (search.md folded into match.md,
      search.md deleted): behavior-neutral on all known fixtures but
      reverses the c910062 loudness split for that patch, and no session
      record explains it — commit with rationale or revert
- [x] Add patches for the v2.1.221 shape — mechanical ones first, the
      two rewrites last since they are opinion rather than drift
  - [x] `strip-duplicate-parallel-tools` (dotfiles@0485a57). Premise
        corrected: no captured body duplicates the directive — the closing
        line seen in live sessions is the API-side tools preamble
        (server-generated from the `tools` param, never in the request, so
        unpatchable). The patch instead strips the in-prompt copy that
        preamble duplicates: the harness bullet's trailing sentence
        (opus/fable) and sonnet's whole ~380-char bullet (byte-stable
        v2.1.76→221)
  - [x] `strip-agent-prohibitions` (dotfiles@70d67e3). Premise corrected:
        the agent-types listing rides in user-turn system-reminders, not
        the system prompt — syspatch can't touch it. "Strip one, decide
        which" was decided by reachability: stripped the opus-only
        `Do not call the AgentTool`/workflows prohibition lines, which
        also contradict standing user config
  - [x] `strip-scratchpad-bloat` (dotfiles@88e946c): condensed to one
        sentence + dynamic path, kept via replace-side `$NAME` expansion —
        a new syspatch feature (mitmproxy@3cf4b8b; replace.md was
        previously literal-only)
  - [x] `condense-delivering-work` (dotfiles@7930800): ~450 → ~130 words,
        every distinct instruction kept; verbatim search so upstream edits
        are a loud miss prompting a re-condense
  - [x] `condense-corrections` (dotfiles@7710992): ~250 → ~70 words, same
        design. Final v2.1.221 deltas: opus −4035 (37%), fable −2006
        (20%), sonnet −5102 (18%)
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
      silent. After the patches, so the baseline it records is a real one.
      Design input (2026-08-04): must be **per-shape, across all promoted
      live shapes** — a single global number is dominated by whichever
      shape happened to be captured (live shapes strip at 9%/11%/16%), and
      checking only the newest unsuffixed fixture would have missed this
      exact incident (the sonnet long-form kept stripping fine while the
      opus/fable shapes went dark)
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
