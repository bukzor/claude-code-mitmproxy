#!/bin/sh
# Method for 2026-08-18-005-rss-after-user-ran-view-clear.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'ps -o pid,rss,etime,args -p 31950; grep -E "VmRSS|VmHWM" /proc/31950/status'
