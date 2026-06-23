# Todo

- [ ] Verify patch-failure capture end-to-end live: run `proxy.sh`, route Claude
  Code through it, induce a patch miss (e.g. stale `match.md`); confirm the
  `logging.warning` flashes in the mitmproxy status bar and the records land
  under `patch-failures/_bodies/{digest}.md` + `patch-failures/{rule}/{digest}.json`.
  (Curses behavior is so far asserted from mitmproxy 12.2.1 source, not
  observed. The content-addressed/dedup recorder was reworked 2026-06-23 and
  tested offline only — live capture still unverified.)
