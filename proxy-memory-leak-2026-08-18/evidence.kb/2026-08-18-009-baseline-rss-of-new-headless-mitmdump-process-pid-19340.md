---
captured: "2026-08-18"
method: ./2026-08-18-009-baseline-rss-of-new-headless-mitmdump-process-pid-19340.sh
---

# Baseline RSS of new headless mitmdump process, pid 19340

```sh
'bash' '-c' 'ps -o pid,rss,etime,args -p 19340; grep -E "VmRSS|VmHWM" /proc/19340/status'
```

```
  PID   RSS     ELAPSED COMMAND
19340 99284       02:42 /home/bukzor/claude/mitmproxy/.venv/bin/python /home/bukzor/claude/mitmproxy/.venv/bin/mitmdump --mode reverse:https://api.anthropic.com --listen-port 8080 --set flow_detail=0 -w +/home/bukzor/claude
VmHWM:	   99284 kB
VmRSS:	   99284 kB
```
