#!/bin/sh
# Method for 2026-08-18-004-vmrss-after-user-ran-view-clear.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'date -Is; grep -E "VmRSS|VmHWM" /proc/31950/status'
