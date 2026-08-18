#!/bin/sh
# Method for 2026-08-18-008-baseline-rss-of-new-headless-mitmdump-process.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'ps -o pid,rss,etime,args -p "$(pgrep -f bin/mitmdump)" ; grep -E "VmRSS|VmHWM" "/proc/$(pgrep -f bin/mitmdump)/status"'
