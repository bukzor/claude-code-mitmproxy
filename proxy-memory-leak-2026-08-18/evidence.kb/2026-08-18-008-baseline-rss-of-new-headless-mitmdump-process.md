---
captured: "2026-08-18"
method: ./2026-08-18-008-baseline-rss-of-new-headless-mitmdump-process.sh
---

# Baseline RSS of new headless mitmdump process

```sh
'bash' '-c' 'ps -o pid,rss,etime,args -p "$(pgrep -f bin/mitmdump)" ; grep -E "VmRSS|VmHWM" "/proc/$(pgrep -f bin/mitmdump)/status"'
```

Exited 2.

```
error: process ID list syntax error

Usage:
 ps [options]

 Try 'ps --help <simple|list|output|threads|misc|all>'
  or 'ps --help <s|l|o|t|m|a>'
 for additional help text.

For more details see ps(1).
grep: /proc/19340
19562
19623
19639/status: No such file or directory
```
