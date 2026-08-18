# Host and proxy topology

As of 2026-08-18.

- VM guest (Chromebook/crostini-style kernel 6.6.99-09128-g14e87a8a9b71),
  8 CPUs, 14.5 GiB RAM, **no swap**; root disk 137 GB (32 GB free).
- Proxy: `proxy.sh` runs mitmproxy 12.2.3 on Python 3.13, in tmux,
  reverse mode toward api.anthropic.com on :8080,
  `-w +log/traffic/%Y-%m-%d.flow`, six `-s` addons, flow2jsonl to
  `log/traffic/%Y-%m-%d.jsonl`. Since the 2026-08-18 15:42 restart the
  script execs headless `mitmdump` (`flow_detail=0`, event log on
  stderr); the incident-era process was the interactive **TUI**. A
  seventh addon, `quietconn.py`, was added afterward (see
  `../remediations.kb/run-headless-mitmdump.md`).
- Every flow is persisted to disk twice (raw .flow and .jsonl), so the
  TUI's in-memory flow store is never the only copy.
- Coresident memory consumers: several `claude` sessions at 500-630 MiB
  each.
- Monitoring: none exists for proxy RSS (nothing would have alerted
  before an OOM kill).
