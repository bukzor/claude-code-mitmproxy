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

`masks.d/` follows the same rule, and used not to. `incidents.masks()`
was `functools.cache`d, so a live proxy served the mask set it started
with. Masks *are* the digest function, and the argument was that
re-reading them per request would re-key content mid-run -- the one
thing content-addressing may not do. That argument doesn't survive
contact: a restart re-keys just the same, only later and out of the
editor's sight. On 2026-08-09 the restart itself minted duplicate
old-scheme captures within seconds of coming up. What actually must not
happen is a *single* body split across two mask sets, and that is
enforced at the call sites instead: each masks once and threads the
resulting text through (`incidents.digest_of`). So edit a mask and
there is nothing else to do -- `log/prompt-captures/` is named by raw
digests no mask edit can move, and its dedup index re-derives itself
the first time the mask set stops comparing equal
(`design/040-design.kb/content-addressed-capture.md`).

A stat-keyed cache was the obvious middle road and isn't worth it.
Fingerprinting `masks.d/` costs 390us of `stat`, loading it costs 658us,
and the masking those files then do costs ~1ms regardless: the cache
nets a quarter of a millisecond, once per request, for an extra function
and a parameter that exists only to be a cache key.
