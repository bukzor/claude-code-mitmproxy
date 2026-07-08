---
why:
  - decoupled-from-the-cli
  - pristine-fixture-supply
---

# Addon pipeline

One mitmproxy addon per concern; `proxy.sh`'s `-s` order is the
dataflow, because mitmproxy runs each hook in addon load order:

    syscapture → syspatch → toolpatch → thinkpatch → flow2jsonl

`syscapture` is first because it must see the wire-original request.
`flow2jsonl` is last deliberately: the log records what was actually
sent, which is what you want when verifying patches live. Fixtures come
from `syscapture`, never from the log (see `fixture-lifecycle.md`).

Reordering these breaks invariants nothing else enforces.
