---
why:
  - ../../020-goals.kb/ease-of-operation.md
---

# Rotation self-heals instead of trusting `_current_path` alone

`addons/flow2jsonl.py`'s `_rotate_if_needed` must treat "no open file" as its own
reason to (re)open, not just "the formatted path changed". Checking
`path == _current_path` alone lets `_fp` and `_current_path` fall out of
sync -- once that happens, every later call sees the path still matches
and short-circuits without ever reopening, so `_emit` writes nothing and
raises `AssertionError` on every request for the rest of the day. The
process only recovers when the date rolls over and `path` finally stops
matching the stale `_current_path`.

This bit for real on 2026-07-25: the running proxy went dark for the
capture file (`log/patch-failures/_uncaught-flow2jsonl/`, archived) for
several hours, silently, recovering only at midnight. `_rotate_if_needed`
now requires both `path == _current_path` *and* `_fp is not None` to
skip reopening, and nulls `_fp` immediately after closing it so a failed
reopen can't leave a stale, truthy handle behind either. A broken
invariant is now repaired on the very next call instead of waiting for a
date boundary.
