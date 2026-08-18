#!/bin/sh
# Method for 2026-08-18-003-rss-growth-sample-12-x-20s.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'for i in $(seq 12); do printf "%s " "$(date -Is)"; grep VmRSS /proc/31950/status; sleep 20; done'
