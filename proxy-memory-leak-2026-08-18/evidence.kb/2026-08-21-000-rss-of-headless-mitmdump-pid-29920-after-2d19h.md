---
captured: "2026-08-21"
method: ./2026-08-21-000-rss-of-headless-mitmdump-pid-29920-after-2d19h.sh
---

# RSS of headless mitmdump, pid 29920, after ~2d19h of live traffic

```sh
'bash' '-c' 'ps -o pid,rss,etime,args -p 29920; grep -E "VmRSS|VmHWM" /proc/29920/status'
```

```
  PID   RSS     ELAPSED COMMAND
29920 141120 2-18:36:02 /home/bukzor/claude/mitmproxy/.venv/bin/python /home/bukzor/claude/mitmproxy/.venv/bin/mitmdump --mode reverse:https://api.anthropic.com --listen-port 8080 --set flow_detail=0 -w +/home/bukzor/claude
VmHWM:	  141120 kB
VmRSS:	  141120 kB
```

`pid 29920` is the process `324b7e4` (2026-08-18 16:01:05 -05:00, "Run the
proxy headless: mitmdump, plus a connection-chatter cap") started at reload
-- not the 15:42 `pid 19340` this incident's baseline capture
(`2026-08-18-009-...`) recorded, but the same headless-mitmdump remediation,
restarted ~19 min later by that commit landing. Baseline for *this* pid is
therefore the `~99 MiB` `pid 19340` baseline read a few minutes earlier
(no separate baseline capture was taken for 29920's first minutes).

Growth since: ~99 MiB -> 141 MiB over ~66.6 h = ~0.63 MiB/h. The original
leak grew ~526 MiB in 28 h = ~18.8 MiB/h -- about 30x faster. `VmHWM ==
VmRSS` still (no observed shrink), consistent with normal heap growth/
fragmentation for a long-lived Python process under real traffic, not a
reintroduced per-flow retention leak.
