---
captured: "2026-08-18"
method: ./2026-08-18-004-vmrss-after-user-ran-view-clear.sh
---

# VmRSS after user ran view.clear

```sh
'bash' '-c' 'date -Is; grep -E "VmRSS|VmHWM" /proc/31950/status'
```

```
2026-08-18T15:09:17-05:00
VmHWM:	  578908 kB
VmRSS:	  578908 kB
```
