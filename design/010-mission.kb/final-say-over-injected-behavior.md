# Final say over injected behavior

Claude Code hardcodes the text it injects into every request — system
prompt, tool descriptions, beta flags — with no configuration surface.
Some of it contradicts the user's CLAUDE.md instructions; some is bloat
billed on every request; some (thinking redaction) removes capability
the API otherwise offers.

This project gives the user final say over what Claude Code sends on
their behalf, while staying on the stock, current CLI.

Success looks like: sessions differ from stock only by the intended
edits; CLI upgrades require no rework beyond re-verifying targets; and
upstream drift is noticed by the system, not discovered by the user.
