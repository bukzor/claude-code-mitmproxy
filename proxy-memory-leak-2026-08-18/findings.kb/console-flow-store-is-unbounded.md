---
status: confirmed
evidence:
  - "mitmproxy 12.2.3 source: .venv/lib/python3.13/site-packages/mitmproxy/addons/view.py:149 (_store OrderedDict; removal only via view.clear / view.flows.remove / filtered kill)"
---

# mitmproxy 12.2.3's console View addon stores every flow, with no eviction

`View._store` is a plain OrderedDict populated on every request
(view.py:517-518) and emptied only by explicit user commands. There is
no size cap or TTL option. This is by design for an interactive tool --
the flow list *is* that dict -- but it makes the TUI unsuitable for
unattended long-running capture: memory is proportional to total bytes
proxied since start (or since the last manual clear).
