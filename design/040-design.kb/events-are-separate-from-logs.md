---
why:
  - ../020-goals.kb/earned-attention.md
---

# Events are separate from logs, and the logger name is the interface

A log line is prose for whoever is watching. An event is a *fact the proxy
learned exactly once* -- "this prompt body had never been seen before" -- and a
consumer wants it as a line in a tailable file, not as prose in a mixed stream.
Before this, both went to stderr and `proxy.sh` captured neither, so the proxy
announced its news once and discarded the announcement.

Records under `claude_mitmproxy.events` are the second kind. The logger name
*is* the path: `…events.capture.system-prompt` writes
`log/events/capture/system-prompt.<date>.log`, so a consumer subscribes by
tailing a file and parses nothing.

## What earns a segment

A segment is warranted when there is a good chance some future handler, filter
or level would want to treat its contents differently -- not only when a
consumer would watch that subtree today. Logger names are a configuration
surface, and config-time differentiation is the use you cannot enumerate in
advance; since a segment costs one dotted name, the bar is deliberately low and
the categorization is formed ahead of the need.

Segments name message **categories**, never the module that emitted them. An
emitter is an implementation detail, so welding it into the name makes an
ordinary refactor a breaking change to something people tail.

The ratified taxonomy, spelled once in `logging_handlers` because these strings
are published:

| Domain | Types |
| --- | --- |
| `capture` | `system-prompt`, `subagent-prompt` |
| `incident` | `patch-miss`, `strip-floor`, `uncaught` |
| `lifecycle` | `startup`, `reload` |
| `housekeeping` | `gc`, `compress` |

## What this does not change

Records still propagate to the root logger, so mitmproxy's `TermLogHandler`
prints them for an operator watching interactively
(`../../CLAUDE.kb/console-output-bands.md`). Leaving mitmdump's own event log on
stderr is deliberate: that stream is for watching a proxy, not for consuming.

The events logger sets its own level rather than inheriting one. Whether a
durable record gets written must not depend on how loud the console is --
mitmproxy sets root to `DEBUG` and a bare CLI leaves it at `WARNING`, and the
file has to say the same thing under both.

Loudness is unaffected: [loudness-policy] still decides what warrants an
incident and a status-bar flash. An event file is a record, not an alarm.

## Testing note

> Agent-authored and vetoable. The facts below were verified in this repo, but
> stating them as a rule future sessions follow is a session's choice, not a
> ruling.

Do not assert propagation with pytest's `caplog`. Its logging plugin captures
records by a route that survives `propagate = False`, so such a test passes
against a handler that has stopped reaching the root entirely. Attach a handler
of your own to the root logger instead.

[loudness-policy]: loudness-policy.md
