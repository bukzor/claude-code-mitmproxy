# The traffic log is what we sent, never what Claude Code sent

`proxy.sh` loads `flow2jsonl.py` **last** of the `-s` addons, after `syspatch.py`
and `toolpatch.py`. mitmproxy runs request hooks in load order, so by the time
the dump addon serializes a flow, every patch has already been applied. Each
record in `log/traffic/YYYY-MM-DD.jsonl` is therefore the request that went
upstream, not the request the client handed us. The `.flow` dump beside it is
written by mitmproxy's own writer at flow completion, so treat it the same.

Consequence: the traffic log cannot answer "what did upstream serve?" or "what
does the client send?" for anything a rule touches. A patched body in the log is
our own output, read back.

## The trap this sets, concretely

A deletion leaves a scar whose shape invites a wrong conclusion. The auto-mode
steer rides in a `role: "system"` bulletin as

```
While auto mode is active:

<steer body>

Today's date is 2026-09-23.
```

`retune-auto-mode-bash-steer` deletes `<steer body>\n`, so the logged record
reads `While auto mode is active:\n\n\nToday's date is 2026-09-23.` -- three
newlines where the body was. Read as *input*, that looks like upstream putting a
benign date notice directly under the auto-mode heading, which in turn implies
the rule's `match` hits an envelope with no steer in it and files a false alarm
every turn.

It does not, and cannot. Claude Code builds the system message from its own
session state each turn and has no knowledge of the rewrite, so the pristine text
arrives on every request and is re-deleted on every request. The scar is never an
input, and the rule cannot match its own output.

Measured, on the pristine window before the rule landed (2026-09-01 .. 09-16, 16
days, 80 distinct heading-bearing `role: "system"` messages): **100% steer-first,
zero three-newline forms.** Three-newline forms appear only from 2026-09-17, the
day the rule went live. The scar is ours.

Two separate sessions reached the false-alarm conclusion from the log before this
was written down, which is why it is written down.

## Where to look for pristine text instead

- **`system`** -- `system-prompts.kb/` fixtures, captured by `prompt_capture.py`
  upstream of patching. That is the whole point of a separate capture path.
- **`tools[].description`** -- the `upstream.d/` files under
  `~/.config/claude-mitmproxy/tool-description.d/`, which hold the verbatim
  upstream wordings an exact-compare tripwire comes from.
- **`messages[]` with `role: "system"`** -- nothing. This locus has no pristine
  capture, which is exactly why the trap is live here and nowhere else. Until
  that exists, the only sound reading of the log at this locus is of traffic
  recorded before the relevant rule existed.
