# incident.patch-miss

A patch failed to apply to a body, and the record is waiting in
`log/patch-failures/<rule>/`. The watch's line counts live records per
rule -- `tooldesc-Bash=3` is three bodies the `tooldesc-Bash` patch missed
-- and it changes as records are archived, disappearing with the last.

Addressing it is triage, `CLAUDE.kb/patch-failure-triage.md`: read the body
the record names, decide what upstream did to the patch's target, fix or
retire the patch, then `archive_incident`. That decision is judgment about
someone else's prose, which is why this line reaches a reader at all; the
queue's upkeep does not, since a proxy start sweeps it.
