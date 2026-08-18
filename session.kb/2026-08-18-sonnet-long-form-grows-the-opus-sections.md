# 2026-08-18: sonnet's long-form grows the opus sections

## How it surfaced

Routine maintenance: nine live incidents in `log/patch-failures/`, all
Aug 14–18, plus a `survey_captures.py` pass. None of it was an outage —
every mechanism did its job; this entry records what the pile meant.

## What the incidents were

Seven were `tooldesc-*` `changed-upstream`, all arriving with cc 2.1.232
(pinned by correlating incident timestamps against billing headers in the
Aug 14 traffic shard):

- Bash long-form description regrew the full `# Committing changes with
  git` procedural section (the short `# Git` section, expanded back to the
  old protocol), in all four model stamps — Sonnet 5, Opus 5, Opus 5 (1M),
  Fable 5. The stub and `must-read.kb/before/git/` already cover its
  substance; accepted as `upstream.d/long-form-{model}-2.1.232.md`.
- A first sighting of the harness-short Bash wording with a Sonnet 5
  Co-Authored-By stamp (`harness-sonnet.md`) — sonnet sessions now receive
  the harness-family tool wording too.
- Minor rewordings of Agent (fork paragraph gains the don't-fabricate-
  pending-results sentence) and SendMessage (bare-name delivery clause
  expanded). Both already covered by the stubs; accepted.

Two were `_locate-system-prompt` `found-0-prompt-bodies`: the session-title
prompt reworded again at 2.1.234 ("You are naming a coding session…"), and
a new auxiliary shape at 2.1.232 — an auto-mode configuration proposal
generator ("You transform a mechanically-gathered recon block…"). Both
genuinely non-interactive; added to `AUX_TASK_PREFIXES`.

## The real finding: shape drift at 2.1.233

`survey_captures.py` showed every current shape's core unpromoted since
2.1.226/227, and one anomaly: a 20KB *sonnet* capture at 2.1.233.89c
classified `harness-opus`. Hand-diffing showed it is sonnet's long-form
body with the previously opus-only `# Delivering work` and `# Corrections`
sections appended (replacing the autonomy paragraphs), plus two
experiment-smelling trailer lines ("Do not call the AgentTool…").

That broke `prompt_shape.py`'s naming premise: `# Delivering work` is no
longer unique to the opus harness shape. Marker order was `# Delivering
work` before `# Doing tasks`, so the hybrid classified harness-opus — and
promoting it under that shape would have poisoned the harness-opus strip
floor (a long-form-family core inflating the floor above what real opus
sessions strip: exactly the false-loudness `earned-silence` forbids).

Fix: reorder `SHAPE_MARKERS` so `# Doing tasks` (still unique to the
long-form family) wins before `# Delivering work`. The hybrid is
long-form; true opus bodies, lacking `# Doing tasks`, still classify
harness-opus. `check_strip_floors.py` validated the reorder against all
69 captures offline.

## What changed

- `upstream.d/` gains seven accepted tool-description wordings.
- `AUX_TASK_PREFIXES` gains the two new auxiliary openings.
- `SHAPE_MARKERS` reordered as above.
- Promoted fixtures: `v2.1.232.md` (the fa6 build's core — newer wording,
  carrying the "mid-conversation system turns" phrasing, over the
  concurrent da8/cd0 core), `v2.1.232-fable.md`, `v2.1.232-opus.md`,
  `v2.1.233.md` (the hybrid — now the default `check_patches` fixture).
  All checks zero-warning; floors moved harness-opus 1502→1563,
  long-form 2551→3624.
- Stale doc claim fixed in two places: `check_patches` takes no capture
  argument (variants are covered by `check_dark_patches.py`'s matrix).
- All nine incidents archived; gc pruned two expired archive files.

## Open question

The hybrid is a single capture from one build, with trailer lines that
read like a server-side experiment. If sonnet reverts, `v2.1.233.md`
stays valid as a record but the next promotion supersedes it; if the
other models converge on the hybrid too, the harness shapes may collapse
back into one — watch the survey.
