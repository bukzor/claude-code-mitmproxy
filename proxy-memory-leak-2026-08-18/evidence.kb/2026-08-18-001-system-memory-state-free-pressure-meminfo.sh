#!/bin/sh
# Method for 2026-08-18-001-system-memory-state-free-pressure-meminfo.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' 'free -m; cat /proc/pressure/memory; sed -n 1,12p /proc/meminfo'
