---
why:
  - ease-of-operation
---

# Sharded logs

Any output whose size has no natural bound -- currently the live
`traffic.{flow,jsonl}` capture -- is written to a strftime-templated path
(`log/traffic/%Y-%m-%d.flow`), never a fixed filename: each day gets its
own shard, so a restart-free run doesn't grow one file forever and
`find -size +1G` never becomes the normal state of the repo.

Content-addressed outputs (`log/patch-failures/`, `log/prompt-captures/`)
don't need this: each item is small and named by its own hash, so the
directory can only grow by distinct content, never by wall-clock time.
