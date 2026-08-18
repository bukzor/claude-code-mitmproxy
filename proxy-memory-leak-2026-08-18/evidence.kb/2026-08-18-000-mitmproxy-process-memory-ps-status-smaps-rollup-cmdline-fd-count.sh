#!/bin/sh
# Method for 2026-08-18-000-mitmproxy-process-memory-ps-status-smaps-rollup-cmdline-fd-count.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'ps -o pid,ppid,rss,vsz,etime,args -p 31950; cat /proc/31950/status /proc/31950/smaps_rollup; tr "\0" " " < /proc/31950/cmdline; echo; ls /proc/31950/fd | wc -l'
