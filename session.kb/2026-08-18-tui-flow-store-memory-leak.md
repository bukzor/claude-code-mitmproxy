# 2026-08-18: the TUI's flow store ate half a gig

## What happened

The user noticed the proxy at ~526 MiB RSS after 28 h and climbing.
Root cause, confirmed the same afternoon: `proxy.sh` ran the interactive
mitmproxy TUI, whose view store retains every flow with no eviction --
harmless for casual use, but this proxy relays Claude Code's
hundreds-of-KB request bodies all day, so the store grows at traffic
rate (~93 MB/h busy). The decisive test was a post-`view.clear` plateau:
+4 kB RSS over 15 minutes while ~57 MB of flows crossed the wire.

Full forensics -- evidence captures, timeline, competing root causes,
remediation status -- in `../proxy-memory-leak-2026-08-18/`.

## Why nothing was loud

Nothing was supposed to be. The growth was inside a healthy process
(no OOM, no fd leak, host had headroom), and no monitoring watches
proxy RSS -- the first alarm would have been the kernel's. The user's
own observation was the detector.

## What changed

`proxy.sh` now execs headless `mitmdump` (`flow_detail=0`, event log on
stderr -- the only TUI feature in use was the `E` screen). A new
`quietconn.py` addon caps the `mitmproxy.proxy.server` logger at
WARNING, since headless operation surfaced 4-6 connect/disconnect lines
per API call that buried the deliberate loudness. Baseline after
restart: ~97 MiB. Day-after RSS is the outstanding fix verification
(`../proxy-memory-leak-2026-08-18/todo.kb/`).
