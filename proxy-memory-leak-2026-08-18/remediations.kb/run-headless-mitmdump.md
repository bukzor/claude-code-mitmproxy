---
status: done
requires-sudo: false
---

# Run mitmdump instead of the TUI (adopted fix)

The user only ever used the TUI for the `E` event log, so `proxy.sh` now
runs `exec mitmdump --set flow_detail=0` with stdout redirected to
stderr: same addons, same disk capture, event messages on stderr, and no
view store to grow. Edited and smoke-tested 2026-08-18 (all addons load,
listener up, messages on stderr); adopted by the user's restart at
15:42:18 (PID 19340, baseline ~97 MiB).
Supersedes `cap-view-store-with-addon.md`. The root
cause was confirmed independently by the post-clear plateau; a day of
bounded RSS under mitmdump is fix verification.

Follow-up, same day: the event log the TUI kept on its `E` screen now
streams to stderr, and its per-connection chatter (4-6
`client/server (dis)connect` lines per API call) buried the messages the
proxy is deliberately loud about. A seventh addon, `quietconn.py`, caps
the `mitmproxy.proxy.server` logger at WARNING. Smoke-tested (chatter
gone, startup messages and a proxied request unaffected); takes effect
at the next restart, since a new `-s` line does not hot-load.
