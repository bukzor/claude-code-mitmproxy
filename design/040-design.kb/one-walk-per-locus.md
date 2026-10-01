---
why:
  - ../020-goals.kb/pristine-fixture-supply.md
  - ../020-goals.kb/earned-silence.md
  - ./prompt-loci-coverage.md
---

# One walk per locus

> [!TODO] Nothing below is built. `prompt-loci-coverage.md` states which
> surfaces are covered; this entry states how coverage is declared, and the
> declaration does not exist yet.

> [!DRAFT] agent-authored 2026-10-01, vetoable, except where marked
> otherwise. The empirical claims are measured; the design is inferred and has
> not been ruled on.

Every behavior-shaping surface is one row of a locus table, and the only
per-locus code is the walk -- where in a request that locus's text lives, and
which requests legitimately carry none of it. Capture, dedup, masking,
promotion, fixture naming, the strip-rate floors, the offline checks and the
monitoring parametrization are all locus-independent and take the row as
input.

The table being the single enumeration is the point. A surface classified once
in prose, with each consumer re-deriving the list, is how a locus gains an
occupant that nothing watches: the coverage note that spared
`<system-reminder>` envelopes by policy was sound for the surface it was
written about and silently failed to reach `messages[]` entries when an
injection arrived there. `prompt-loci-coverage.md` is therefore derived from
the table rather than maintained beside it, so a surface cannot be documented
as covered while no machinery is attached to it.

## Both directories derive from the locus name

A locus needs two directories, and neither is chosen:

- `~/.config/claude-mitmproxy/{name}.d` -- the rules, which are the
  operator's.
- `{repo}/{name}s.kb` -- the accepted upstream text, which is Anthropic's.

The split is one of authority, not of convenience: rules are personal
configuration and live in the personal repo, while captured upstream prose is
project data and lives in the project repo. One path per authority per locus,
so a new locus's directories follow from its name and `survey_captures.py` and
`prompt_patches.py` stop holding the same constant twice.

"Never patched" and "never promoted" are then values a row takes, not
positions in a directory tree. `prompt-captures/subagents/` exists today only
so the promotion pass does not enumerate bodies that are never patched; a row
that declares its own attachments says that directly.

## The shape is the key the walk yields

Classification happens once, in the walk, and is persisted in the capture
filename. Offline consumers -- `check_strip_floors.py`, `survey_captures.py`
-- read the key rather than recomputing it from a globally reachable marker
table, which is the same single-enumeration argument one level down:
`prompt_shape.shape_of` is called from four places today, each re-deriving
what the capture already knows.

A locus with structural variants supplies a marker table privately; a locus
without one yields the natural key it already has, such as a tool name. Both
are the same statement -- the shape is the key -- rather than two cases.

## Four roles, one patch engine

The dialect's `search` carries two jobs that coincide for a surgical patch and
diverge for a whole-body one: it selects the region to overwrite, and it
asserts that the content is what was last reviewed. Separating them collapses
`tool_patches.py`'s exact-compare into the template engine, because the
behavior each needs then follows from the data instead of from which engine
ran:

> [!@bukzor] ruled 2026-10-01. The factoring below is the operator's, quoted:
> "The write region is search. / Search, if absent, defaults to match." The
> agent had written it as one three-armed conditional; stating it as a
> definition plus a chain of defaults is what makes the whole-body case a
> default rather than a value a rule declares, and the completion of the chain
> to `expect` and to the whole body follows the same form.

- `match` answers whether the rule is in scope here. A miss is silent, which
  is how a rule detects its own irrelevance.
- `expect` answers whether the content is what was last reviewed. A miss is
  loud.
- The write region **is** `search`.
- `search`, absent, defaults to `match`; `match`, absent, defaults to the
  whole body; `expect`, absent, defaults to `search`.

A rule may write exactly when its write region exists. A tool stub names
neither `match` nor `search`, so its region is the whole description and the
stub installs even when `expect` misses -- which is what a self-contained
replacement requires, since drift would otherwise ship the unpatched text. A
surgical rule's region is the text it failed to recognize, so no write is
possible. Neither behavior is configured, and the pair supersedes the
`match`/`search` paragraph in `template-patch-model.md`.

Because the whole body is what the defaults yield rather than something a rule
declares, no placeholder spans it and none is offered. The load-time assert
becomes that a rule says at least one thing about what it expects to find --
at least one of `match`, `search`, `expect` -- which still catches the
half-created rule directory that "match required" was protecting against.

## Loudness follows the patch style, not the locus

A whole-body replacement destroys the pristine text, so an unreviewed body
must be loud. A surgical patch self-reports its misses, so an unreviewed body
is routine and capture plus promotion suffices. That is why
`tooldesc-*/changed-upstream` and a prompt patch's silence on a new release
are both correct, and it decides the question for a new locus without a
judgment call.

## Novelty at an occasion-driven locus

Where a locus's text arrives on every request, "what is upstream serving at
the newest release" is a meaningful question, and `survey_captures.current_drift`
answers it by filtering to the newest release across every shape -- a shape
absent from newer releases being one upstream stopped serving.

`messages[]` entries with `role: "system"` break that inference. Their
occurrence is occasion-driven: a plan-mode notice arrives when a session exits
plan mode, so absence from the newest release carries no information about
upstream. Novelty at such a locus is therefore reported per arrival, through
the incident queue under an underscore-keyed rule, rather than through the
promotion pass. The queue is already content-addressed, already deduped,
already counted per rule and already printed as a keyed line with a
`playbook.kb/` entry, and it already hosts non-rule keys.

The same property defeats aggregate dark-detection here. A strip-rate floor
asks whether a body stripped at least what its shape's sparsest fixture
strips, which is answerable only when a body of that shape arrives; where
arrivals cannot be expected, the floor reports nothing. Per-arrival novelty is
the available signal, not a weaker version of the floor.

## Recognition is measured, not enumerated

This locus also replays the session's own content -- tool results and file
bodies -- inside `role: "system"` messages, so a walk must tell Claude Code's
own instruction from the conversation's echo. The distinguishing property is
whether a body varies with the session or only with the Claude Code build,
and that is observable: requests carry `X-Claude-Code-Session-Id`, so the
number of distinct sessions a masked digest appears in separates the two
directly. A list of replay openers predicts by enumeration what breadth
measures, and grows a false novelty report with every opener upstream adds.

> [!QUESTION] Unsettled, and each would change what gets built:
>
> - Whether fixture names give shape, scope-partial and raw digest distinct
>   positions. Making the shape equal its own suffix deletes
>   `prompt_shape.FIXTURE_SUFFIX`, but `-doing-tasks` currently occupies the
>   same slot as `-opus` while naming a partial rather than a shape.
> - Whether the long-form shape takes an explicit suffix, renaming the 14
>   currently-bare fixtures. `system-prompts.kb/CLAUDE.md` already holds that
>   vacating the bare name loses nothing.
> - Whether `search` is scoped within the match span. It is not today, so
>   `match` scopes applicability but not the replacement.
> - Whether a walk's traversal becomes jsonifiable data with only its
>   recognition inventory left as code.
> - Whether subagent bodies, once promotion is unconditional, are committed.
> - Whether the message locus is promoted to a kb at all, or left as captures
>   plus queue entries. This turns on the surviving shape vocabulary, which
>   nobody has measured.
