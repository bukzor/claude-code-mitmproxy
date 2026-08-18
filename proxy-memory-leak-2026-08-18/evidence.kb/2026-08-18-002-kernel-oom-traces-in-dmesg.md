---
captured: "2026-08-18"
method: ./2026-08-18-002-kernel-oom-traces-in-dmesg.sh
---

# Kernel OOM traces in dmesg

```sh
'bash' '-c' '(dmesg | grep -iE "oom|out of memory|killed process") || : "no oom lines, exit $?"'
```

```
```
