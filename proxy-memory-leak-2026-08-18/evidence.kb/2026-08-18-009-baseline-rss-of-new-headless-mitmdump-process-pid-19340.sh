#!/bin/sh
# Method for 2026-08-18-009-baseline-rss-of-new-headless-mitmdump-process-pid-19340.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'ps -o pid,rss,etime,args -p 19340; grep -E "VmRSS|VmHWM" /proc/19340/status'
