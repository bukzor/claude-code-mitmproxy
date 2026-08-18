#!/bin/sh
# Method for 2026-08-18-002-kernel-oom-traces-in-dmesg.md -- re-runnable, and fair game to improve in place
# (unlike the capture, which is append-only).
'bash' '-c' '(dmesg | grep -iE "oom|out of memory|killed process") || : "no oom lines, exit $?"'
