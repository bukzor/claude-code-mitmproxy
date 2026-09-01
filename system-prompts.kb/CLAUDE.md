--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-kb)
---

# Captured Claude Code System Prompts

Snapshots of the system prompt body Claude Code sends to the Messages API,
used as input to `check_patches.py` for offline patch validation.

## Naming

`v<MAJOR>.<MINOR>.<PATCH>.md` — full captured body for that cc_version.

`v<MAJOR>.<MINOR>.<PATCH>-<scope>.md` — partial capture covering only the
named section (e.g., `-doing-tasks` for `# Doing tasks` only). Patches whose
targets fall outside that section will report `failed to match` when run
against a partial; that's expected, not a regression.

`v<MAJOR>.<MINOR>.<PATCH>-<variant>.md` — full capture of a *concurrently*
served, structurally distinct prompt shape at that same cc_version. Unlike a
`-scope` partial, this is a complete body — just not the "default" shape.
The suffix names the *shape* (by `prompt_shape.py`'s `SHAPE_MARKERS`, itself
named for the heading that distinguishes it), not the model that happened to
receive it: unsuffixed = the long-form `# System` shape, `-opus` = the
`# Harness` shape with `# Delivering work`, `-fable` =
the `# Harness` shape with `# Communicating with the user`. Earlier captures
use `-harness` for the pre-split Fable-class shape. From v2.1.221 through
v2.1.233 shape correlated 1:1 with model class (sonnet/opus/fable), which is
why the suffix reads like a model name — but at v2.1.237 fable-5 was observed
receiving the `-opus` shape (`# Delivering work`), so don't assume the suffix
predicts the serving model. The model still shows *inside* that shape: across
every capture from v2.1.237 on, opus-5 bodies carry `# Corrections` (12/12)
and fable-class bodies do not (0/4, fable-5 and fable-5.1 alike), and fable-5
goes on receiving `harness-fable` too. So `condense-corrections` reporting
dark on a `-opus` fixture promoted from a fable-class capture is that split,
not drift.
No separate registry to update: a patch scopes itself to a variant just by
anchoring its own `match.md` on a heading unique to that shape (see
`CLAUDE.kb/patch-failure-triage.md`). `check_patches` checks only the
newest *unsuffixed* full capture — variant fixtures are validated by
`check_dark_patches.py`'s matrix.

`v<MAJOR>.<MINOR>.<PATCH>-<variant>-<digest>.md` — one of *several* copies of
one shape at one cc_version. Upstream reworks a shape's copy mid-release, and
both copies keep arriving while sessions that started before the change are
still running. **Promote every one of them.** Nothing needs a single winner:
coverage is a question about the fixture *set* (`promoted_cores` reads them
all), `check_patches` targets only the unsuffixed fixture, and the one
consumer that does pick a per-shape winner — the `_strip-rate` floor — breaks
its own ties by (version, size). The pressure to choose was only ever that two
files cannot share a name.

The digest is the first 8 of the **raw** body's, which the capture filename
already carries — *not* the core digest `--drift` prints. Core digests move
whenever `blocks.d/` changes, and a name that a rule edit can invalidate is
exactly what `design/040-design.kb/content-addressed-capture.md` forbids. To
find the fixture for a reported core, use the raw path in the same row.

Suffix *both* copies when a second appears, rather than leaving the first
bare: which file lacks a digest would otherwise record nothing but which
happened to be promoted first.

> Agent-authored and vetoable: the long-form exception below was decided by a
> session promoting the first pair of concurrent long-form copies, not ruled.

The unsuffixed shape is the exception, because there its bare name is not a
record of promotion order -- `prompt_corpus.latest_fixture()` matches
`^v\d+\.\d+\.\d+\.md$`, so the bare file *is* `check_patches`' target, and
suffixing every copy would silently leave that target pinned to an older
release. One long-form copy keeps the bare name and the rest take digests.
Which one: the largest, matching how `strip_floors` already breaks its own tie
`(version, len(text))`, so the two consumers cannot disagree about which body
is "the" one for that release.

Likewise, patches sunset to `upstream-removed.bool` assert against the
*current* prompt: run against an old capture they report
`matched-despite-upstream-removed`, because the removed text is still present
there. Expected — which is why `check_patches` defaults to the newest capture.

## Adding a capture

Route Claude Code through `proxy.sh`; `syscapture.py` records each unique
prompt body — pristine, pre-patch — to `prompt-captures/` (gitignored) as a
`v<cc_version>_<model>_<digest>.raw.md` / `.md` pair (verbatim / hash-masked
— see `syscapture.py`'s module docstring). Promote the **raw** one by copying:

```bash
cp prompt-captures/v<cc_version>_<model>_<digest>.raw.md system-prompts.kb/v<MAJOR.MINOR.PATCH>.md
```

The masked `.md` sibling has `cwd`/`gitStatus`/etc. replaced with
placeholders — useful for a quick diff, wrong for a fixture: `check_patches.py`
needs pristine text so patch `match.md` anchors see real content.
`prompt-captures/subagents/` holds subagent prompt bodies (Explore, Plan,
claude-code-guide, ...) — captured for visibility, never patched, never
promotion candidates; nothing there belongs in this collection.

Append a `-<variant>`/`-<scope>` suffix per the naming rules above when it
isn't the default long-form shape. Do **not** capture from `traffic.jsonl`
or `traffic.flow`: the proxy records requests *after* patching, so bodies
extracted there are contaminated whenever patches applied cleanly.

## What does not belong

- Patched outputs (regenerable via `check_patches.py`)
- Patch templates (those live in `~/.claude/system-prompt-patches.d/`)
- Non-system-prompt traffic (use `traffic.jsonl` raw)
