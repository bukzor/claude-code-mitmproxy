#!/bin/sh
# Method for 2026-08-18-006-rss-flat-line-watch-after-clear-15-x-60s.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'for i in $(seq 15); do printf "%s " "$(date -Is)"; grep VmRSS /proc/31950/status; sleep 60; done'
