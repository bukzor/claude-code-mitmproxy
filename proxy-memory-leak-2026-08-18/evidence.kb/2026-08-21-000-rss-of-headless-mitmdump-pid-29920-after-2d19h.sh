#!/bin/sh
# Method for 2026-08-21-000-rss-of-headless-mitmdump-pid-29920-after-2d19h.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'ps -o pid,rss,etime,args -p 29920; grep -E "VmRSS|VmHWM" /proc/29920/status'
