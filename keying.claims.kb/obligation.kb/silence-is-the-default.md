---
label: SILENT_DEFAULT
standing: bare
---

# Silence Is the Default

An invariant with no named detector is silent, and silence is the state a
requirement arrives in. Loudness is a thing someone built; nothing about
stating a requirement in prose, a README, or a docstring causes its
violation to be observed.

This follows from what a detector is. A violation becomes observable only
where some execution path evaluates a predicate that the violation
falsifies and reports the result. Absent such a path, the violated and
unviolated states are indistinguishable to every observer, so the system
cannot behave differently between them -- which is what "silent" says.

The consequence worth keeping: enumerate requirements by their detectors,
not by their statements. A requirement stated in three documents and
detected nowhere is one silent requirement, and a requirement no document
states but a test evaluates is a loud one.
