---
captured: "2026-08-18"
method: ./2026-08-18-000-mitmproxy-process-memory-ps-status-smaps-rollup-cmdline-fd-count.sh
---

# mitmproxy process memory: ps, status, smaps_rollup, cmdline, fd count

```sh
'bash' '-c' 'ps -o pid,ppid,rss,vsz,etime,args -p 31950; cat /proc/31950/status /proc/31950/smaps_rollup; tr "\0" " " < /proc/31950/cmdline; echo; ls /proc/31950/fd | wc -l'
```

```
  PID  PPID   RSS    VSZ     ELAPSED COMMAND
31950 31947 538276 1705492 1-03:46:33 /home/bukzor/claude/mitmproxy/.venv/bin/python /home/bukzor/claude/mitmproxy/.venv/bin/mitmproxy --mode reverse:https://api.anthropic.com --listen-port 8080 -w +/home/bukzor/claude/mitm
Name:	mitmproxy
Umask:	0022
State:	S (sleeping)
Tgid:	31950
Ngid:	0
Pid:	31950
PPid:	31947
TracerPid:	0
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
FDSize:	256
Groups:	20 24 25 27 29 44 46 100 101 109 116 999 1000 1001 665357 
NStgid:	31950
NSpid:	31950
NSpgid:	31947
NSsid:	1463
Kthread:	0
VmPeak:	 1705492 kB
VmSize:	 1705492 kB
VmLck:	       0 kB
VmPin:	       0 kB
VmHWM:	  538276 kB
VmRSS:	  538276 kB
RssAnon:	  524628 kB
RssFile:	   13648 kB
RssShmem:	       0 kB
VmData:	  609168 kB
VmStk:	     136 kB
VmExe:	       4 kB
VmLib:	   27580 kB
VmPTE:	    1308 kB
VmSwap:	       0 kB
HugetlbPages:	       0 kB
CoreDumping:	0
THP_enabled:	1
untag_mask:	0xffffffffffffffff
Threads:	17
SigQ:	6/57937
SigPnd:	0000000000000000
ShdPnd:	0000000000000000
SigBlk:	0000000000000000
SigIgn:	0000000001001000
SigCgt:	0000000108084a02
CapInh:	0000000800000000
CapPrm:	0000000000000000
CapEff:	0000000000000000
CapBnd:	000001fcfdfcffff
CapAmb:	0000000000000000
NoNewPrivs:	0
Seccomp:	2
Seccomp_filters:	1
Speculation_Store_Bypass:	thread vulnerable
SpeculationIndirectBranch:	conditional enabled
Cpus_allowed:	ff
Cpus_allowed_list:	0-7
Mems_allowed:	1
Mems_allowed_list:	0
voluntary_ctxt_switches:	90578
nonvoluntary_ctxt_switches:	43244
55626f154000-7ffd9d7c1000 ---p 00000000 00:00 0                          [rollup]
Rss:              538276 kB
Pss:              535959 kB
Pss_Dirty:        524628 kB
Pss_Anon:         524628 kB
Pss_File:          11331 kB
Pss_Shmem:             0 kB
Shared_Clean:       2864 kB
Shared_Dirty:          0 kB
Private_Clean:     10784 kB
Private_Dirty:    524628 kB
Referenced:       538276 kB
Anonymous:        524628 kB
KSM:                   0 kB
LazyFree:              0 kB
AnonHugePages:         0 kB
ShmemPmdMapped:        0 kB
FilePmdMapped:         0 kB
Shared_Hugetlb:        0 kB
Private_Hugetlb:       0 kB
Swap:                  0 kB
SwapPss:               0 kB
Locked:                0 kB
/home/bukzor/claude/mitmproxy/.venv/bin/python /home/bukzor/claude/mitmproxy/.venv/bin/mitmproxy --mode reverse:https://api.anthropic.com --listen-port 8080 -w +/home/bukzor/claude/mitmproxy/log/traffic/%Y-%m-%d.flow -s /home/bukzor/claude/mitmproxy/lib/claude_mitmproxy/addons/reload.py -s /home/bukzor/claude/mitmproxy/lib/claude_mitmproxy/addons/syscapture.py -s /home/bukzor/claude/mitmproxy/lib/claude_mitmproxy/addons/syspatch.py -s /home/bukzor/claude/mitmproxy/lib/claude_mitmproxy/addons/toolpatch.py -s /home/bukzor/claude/mitmproxy/lib/claude_mitmproxy/addons/thinkpatch.py -s /home/bukzor/claude/mitmproxy/lib/claude_mitmproxy/addons/flow2jsonl.py --set jsonl_path=+/home/bukzor/claude/mitmproxy/log/traffic/%Y-%m-%d.jsonl 
28
```
