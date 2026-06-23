# Todo

- [ ] Verify patch-failure capture end-to-end live: run `proxy.sh`, route Claude
  Code through it, induce a patch miss (e.g. stale `match.md`); confirm the
  `logging.warning` flashes in the mitmproxy status bar and the body + `.json`
  land under `patch-failures/{rule}/{date}/`. (Curses behavior is so far
  asserted from mitmproxy 12.2.1 source, not observed.)
