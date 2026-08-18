---
captured: "2026-08-18"
method: ./2026-08-18-003-traffic-volume-since-proxy-start-flow-and-jsonl-shard-sizes.sh
---

# Traffic volume since proxy start: flow and jsonl shard sizes

```sh
'bash' '-c' 'ls -la --time-style=long-iso /home/bukzor/claude/mitmproxy/log/traffic/ | tail -n 8; df -h /home/bukzor/claude/mitmproxy'
```

```
-rw-r--r-- 1 bukzor bukzor   3827973 2026-08-15 19:08 2026-08-15.jsonl.zst
-rw-r--r-- 1 bukzor bukzor   7367301 2026-08-16 17:02 2026-08-16.flow.zst
-rw-r--r-- 1 bukzor bukzor   4083395 2026-08-16 17:02 2026-08-16.jsonl.zst
-rw-r--r-- 1 bukzor bukzor   8361686 2026-08-17 16:28 2026-08-17.flow.zst
-rw-r--r-- 1 bukzor bukzor   4822926 2026-08-17 16:28 2026-08-17.jsonl.zst
-rw-r--r-- 1 bukzor bukzor 176087709 2026-08-18 14:46 2026-08-18.flow
-rw-r--r-- 1 bukzor bukzor 180416779 2026-08-18 14:46 2026-08-18.jsonl
-rw-r--r-- 1 bukzor bukzor         0 2026-08-18 11:13 .compress.lock
Filesystem      Size  Used Avail Use% Mounted on
/dev/vdc        137G  103G   32G  77% /
```
