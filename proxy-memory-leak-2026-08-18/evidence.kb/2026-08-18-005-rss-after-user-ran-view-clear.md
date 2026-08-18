---
captured: "2026-08-18"
method: ./2026-08-18-005-rss-after-user-ran-view-clear.sh
---

# RSS after user ran view.clear

```sh
'bash' '-c' 'ps -o pid,rss,etime,args -p 31950; grep -E "VmRSS|VmHWM" /proc/31950/status'
```

```
  PID   RSS     ELAPSED COMMAND
31950 558600 1-04:12:31 /home/bukzor/claude/mitmproxy/.venv/bin/python /home/bukzor/claude/mitmproxy/.venv/bin/mitmproxy --mode reverse:https://api.anthropic.com --listen-port 8080 -w +/home/bukzor/claude/mitmproxy/log/traf
VmHWM:	  578736 kB
VmRSS:	  558600 kB
```
