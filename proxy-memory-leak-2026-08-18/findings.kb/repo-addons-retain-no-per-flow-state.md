---
status: confirmed
evidence:
  - "code audit 2026-08-18 of lib/claude_mitmproxy/ at the running revision: all six -s addons plus the library modules they delegate to"
---

# This repo's addons hold no per-flow state

Static audit of every `-s`-loaded addon and its library counterparts:
`flow2jsonl` serializes each request/response to the open shard and
drops the reference; `syscapture`/`syspatch`/`toolpatch`/`thinkpatch`
transform the in-flight flow and return; `reload` holds only module
objects. The single module-level mutable container in the request path,
`prompt_capture._CAPTURED` (`lib/claude_mitmproxy/prompt_capture.py:45`),
caches hex-digest sets keyed by capture directory -- bounded by the
count of unique prompts, kilobytes at most. The `-w` flow writer is
mitmproxy's own streaming saver. Nothing repo-side can account for
hundreds of MiB.
