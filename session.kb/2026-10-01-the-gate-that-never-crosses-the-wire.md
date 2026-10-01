# 2026-10-01 -- the gate that never crosses the wire

## What was asked

Two weeks after the auto-mode bash-first steer was found and patched
(`2026-09-17-a-steer-that-arrived-where-nothing-patches.md`), the operator
asked how to shore up reliability and change detection for that rule and for
`system-message.d` generally; whether a rule could match on request flags or
headers; and whether amending flags or headers -- in requests, or in responses
-- would obviate the message patches altogether.

## What the wire says

The rule still fires. At v2.1.286 today's traffic carries nine `role: "system"`
sections reading exactly `While auto mode is active:\n` -- heading, then
nothing -- and one older persisted section reading
`While auto mode is active:\n\n\nToday's date is 2026-09-23.`, where the
doubled blank is the deletion scar and the date notice is a sibling section.
Live steer text appeared 268 times and more in `role: "system"` on 2026-09-16
and 2026-09-17 across v2.1.268 through v2.1.274, and not once since. No
`retune-auto-mode-bash-steer` directory has ever appeared in
`log/patch-failures/`, so the rule has never recorded a search miss.

Nothing on the wire names the assignment. The full request header set is
User-Agent, `X-Claude-Code-Session-Id`, `x-app`, `anthropic-beta`,
`anthropic-version`, `anthropic-dangerous-direct-browser-access`, the
`X-Stainless-*` family, and authorization. The non-prompt body keys are
`model`, `metadata.user_id`, `max_tokens`, `thinking`, `context_management`,
`output_config`, `stream` and `safeguards`. Neither `bashFirst` nor
`tengu_cozy_teapot` appears anywhere. The assignment is resolved client-side
and reaches the wire only as the injected text.

`safeguards` is new and substantial: one entry of type `dangerous_tool_use`
whose `classifier_context` carries `permission_mode`, the whole allow/deny/ask
ruleset with each rule's source, trusted directories, an `auto_mode` block,
git state, repo visibility, `user_identity`, and a `prior_turn_context` list
35 entries long. It does give auto-mode a structured flag -- `permission_mode`
is exactly `"auto"` -- but `bashFirst` is a randomized subset of auto-mode
sessions, so the flag cannot tell a session where a steer was expected from
one where it was not. No flag can produce a dark-rule alarm; only the text
can.

The gate itself is out of reach in flight. Across every traffic log on disk
the only paths this proxy has ever seen are `/v1/messages`,
`/v1/messages/count_tokens` and `/api/hello`. The GrowthBook fetch that
carries `tengu_cozy_teapot` does not cross it.

A smaller finding, unpursued: the billing header's `cc_version` carries a
fourth component that varies within a single release -- `2.1.286.7de` beside
`2.1.286.0b8`, `2.1.280.af7` beside `2.1.280.0c0`. It is the finest-grained
build or bucket token observed, and the only remaining candidate for a
wire-visible assignment signal.

## What was concluded

Amending request flags cannot work and should not be attempted. It cannot
work because the steer is injected client-side before a request exists, so no
request field feeds back into the client's own injection. It should not be
attempted because the only field with leverage is `safeguards`, which is the
input to a dangerous-tool-use classifier and carries the operator's own deny
rules; editing it would weaken that classifier's picture of the guardrails it
is there to enforce.

Amending responses cannot reach the gate, since the gate fetch is not
proxied. Widening the proxy to that host would still leave the value cached in
`~/.claude.json`, so the effect would be deferred and sticky; editing that
cache is overwritten on refresh and the compiled default is `strict`, so it
fails closed against the operator; and `binpatch` could reach it but is
charter-barred from behavior the proxy can rewrite in flight, which this is.
So the text patch stays the guarantee, and no flag work obviates it.

## Claims that did not survive the session

Three of the agent's own positions were withdrawn under examination.

The residual exposure was framed as a reworded steer *heading*, on the
grounds that a `match` miss is silent while a `search` miss is loud. That is
true but secondary. The heading is a section inside a composite bulletin with
siblings, so the live risk is sibling accretion: a `match` of heading, blank
line and one line lands on whichever section comes first, and an upstream
reordering would send the steer through while reporting a miss on a benign
notice.

A whole-body patch's fail-open behavior was derived from its `match` spanning
the whole body. That is a coincidence, not a cause: the span can be
accidental on a short body, which would silently make a surgical rule
fail-open. The cause is that a self-contained replacement knows its own write
region independently of whether it recognized the content.

Strip-rate floors and the unknown-shape alarm were said to transfer to the
message locus for free. Only the alarm does. A floor is answerable when a
body of its shape arrives, and at an occasion-driven locus arrivals cannot be
expected, so the aggregate signal reports nothing.

A fourth, inherited rather than authored: a sibling session's notes described
the recognition predicate this locus needs as a "deny-list." Nothing is
refused anything here, and the permission framing imported a fail-open
argument that does not apply. It is a recognition predicate, of the same kind
as `BODY_MARKER` and `is_auxiliary_system`.

## What changed

No code. `design/040-design.kb/one-walk-per-locus.md` records the locus table,
the derived-directories law, the four dialect roles and their default chain,
and the six questions still open.
`.claude/todo.kb/2026-10-01-003-Unify-pristine-capture-across-loci.md` holds
the breakdown.

Two of the corrections this session intended were already landed by sibling
sessions the same day: `4f840bd` anchored patch templates to line boundaries,
which is the quoted-copy collision this session had been about to document
again, and `6c5dda4` made a file's trailing newline carry no meaning.
`template-patch-model.md` already documented the bound that keeps a hole from
crossing a blank line. The intended `retune-auto-mode-bash-steer/README.md`
correction was left unwritten rather than written from a pre-anchoring reading
of the code.
