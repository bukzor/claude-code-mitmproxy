---
captured: "2026-08-18"
method: ./2026-08-18-001-system-memory-state-free-pressure-meminfo.sh
---

# System memory state: free, pressure, meminfo

```sh
'bash' '-c' 'free -m; cat /proc/pressure/memory; sed -n 1,12p /proc/meminfo'
```

```
               total        used        free      shared  buff/cache   available
Mem:           14486       11120         466         318        3392        3366
Swap:              0           0           0
some avg10=0.00 avg60=0.00 avg300=0.00 total=53607015
full avg10=0.00 avg60=0.00 avg300=0.00 total=45818172
MemTotal:       14834464 kB
MemFree:          477836 kB
MemAvailable:    3446876 kB
Buffers:              72 kB
Cached:          2875012 kB
SwapCached:            0 kB
Active:          5382420 kB
Inactive:        1042420 kB
Active(anon):    3888912 kB
Inactive(anon):        0 kB
Active(file):    1493508 kB
Inactive(file):  1042420 kB
```
