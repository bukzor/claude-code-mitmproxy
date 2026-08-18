---
status: refuted
---

# A repo addon accumulates per-flow data

The natural first suspect, since this repo hangs six scripts off the
proxy. Refuted by static audit
(`../findings.kb/repo-addons-retain-no-per-flow-state.md`): every addon
transforms or serializes the flow and drops it; the only module-level
cache holds digest sets measured in kilobytes.
