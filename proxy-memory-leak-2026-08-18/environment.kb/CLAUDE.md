# Environment

Static context of the machine under investigation, one aspect per file.
Prose-only (no shared lifecycle metadata worth a schema).

Belongs: facts about the system that hold across the incident --
virtualization topology, resource limits, log visibility, monitoring
state.
Does not belong: anything time-stamped to the incident (`../timeline.kb/`)
or captured output (`../evidence.kb/`).

Edit in place when the environment changes (note the date); these files
describe "now", not history.
