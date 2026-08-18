#!/bin/sh
# Method for 2026-08-18-003-traffic-volume-since-proxy-start-flow-and-jsonl-shard-sizes.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'ls -la --time-style=long-iso /home/bukzor/claude/mitmproxy/log/traffic/ | tail -n 8; df -h /home/bukzor/claude/mitmproxy'
