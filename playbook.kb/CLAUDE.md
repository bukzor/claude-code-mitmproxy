# playbook.kb/ -- what addressing a watch line means

One entry per event type in `logging_handlers.events`, named by the key a
printed line starts with: `promotion.refused ...` is looked up as
`promotion.refused.md`. `check_playbook` refuses a commit where the two
disagree in either direction, so adding a type is what occasions an entry
here, and renaming one is what occasions a rename.

Belongs: what a reader does about a line with that key -- the decision, a
pointer to the procedure where one already lives, or the statement that
nothing is asked. A type the watch never prints still gets an entry saying
so, so a key followed from a grep of `log/events/` lands somewhere.

Does not belong: the fact itself (the line carries it), how the event is
produced (the emitting module's docstring), or a procedure long enough to be
its own document (`CLAUDE.kb/`, pointed to from here). An entry is read when
its line arrives, not studied in advance: short, leading with the decision.
