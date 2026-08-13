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

Each addon is hooks and nothing else, living in `lib/claude_mitmproxy/addons/`
with the library it delegates to beside it -- `syspatch` → `prompt_location`
+ `prompt_patches`, `syscapture` → `prompt_location` + `prompt_capture`,
`toolpatch` → `tool_patches`. The offline checks import the library half and
so run the code the proxy runs, without mitmproxy installed; nothing outside
`addons/` may import an addon, which is what keeps that true (asserted by
`reload.py`, explained in `addons/__init__.py`).
