# Evidence captures

Raw command output preserved verbatim, one capture per file, named
`YYYY-MM-DD-NNN-slug.md` by capture date. Frontmatter per
`../evidence.jsonschema.yaml` records when and how each was taken; the
`method` lives in a same-stem sibling `.sh` (re-runnable, shellcheckable),
which unlike the capture may be improved in place.

Belongs: output that future analysis might re-read, especially perishable
sources (dmesg ring buffer, journals subject to vacuuming, process
listings).
Does not belong: interpretation -- that goes in `../findings.kb/` or
`../timeline.kb/`, pointing back here.

Append-only: never edit a capture after filing (trailing interpretation
notes written at capture time are part of the capture). New information
means a new capture file.
