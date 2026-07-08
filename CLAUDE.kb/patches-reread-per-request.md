# Patches are re-read per request, not cached at startup

`syspatch.py` and `toolpatch.py` both used to snapshot their patch
directories once, in `load()` at mitmproxy startup, and serve every
request from that in-memory copy. A running proxy never re-read them,
so editing `*-patches.d/` while the proxy was live produced incidents
describing the *old* config -- including a ghost failure mode where
deleting an incident record under a stale proxy removed the
idempotence guard and the same content hash silently reappeared.
(Observed 2026-07-08: `tooldesc-SendMessage` reappeared minutes after
triage because the live proxy predated the `upstream.d/` adoption.)

Fixed by deleting the cache: both addons now call `load_patches()` /
`load_tool_patches()` fresh inside `_request()`. The patch directories
are a handful of small files, requests arrive at human-interactive
rates, so re-reading them costs nothing measurable. Disk and behavior
can no longer disagree -- edit a patch file and the very next request
sees it, no restart, no triage-ordering to remember. `load()` still
runs at startup but only to log what's configured; it no longer feeds
request handling.
