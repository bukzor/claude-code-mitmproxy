---
why:
  - ../../020-goals.kb/ease-of-operation.md
---

# Safe restart

The sharded path is opened in append mode (leading `+`), because the
alternative is fatal for a long-lived proxy: mitmproxy's default
(`-w path`, no `+`) truncates on open -- fine for a one-shot capture, not
for one restarted mid-day. This bit for real: a plain-filename restart on
2026-07-25 silently discarded 9 days / 4.6G of accumulated capture the
moment the process reopened its `-w` target. `+` plus a same-day path
makes a restart resume instead of erase.

`addons/flow2jsonl.py` reimplements both checks -- rotate on date change, append
within a day -- mirroring mitmproxy's own `save_stream_file` option
(`mitmproxy.addons.save.Save.maybe_rotate_to_new_file`) rather than
inventing a second convention, so both capture files behave identically
across a restart.
