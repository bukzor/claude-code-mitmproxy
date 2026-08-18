---
at: "2026-08-18T15:13:00-05:00"
source: proxy.sh edit in this session; smoke-tested 15:14:38 on port 18081
confidence: observed
---

# proxy.sh switched from the mitmproxy TUI to headless mitmdump

`exec mitmdump` with `flow_detail=0` and stdout redirected to stderr, so
the event log (the messages formerly behind the TUI's `E`) prints to the
terminal and no flow store exists. Takes effect at the next proxy
restart; the live PID 31950 still runs the TUI until then.
