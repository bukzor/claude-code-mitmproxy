---
label: DISSOLVE
standing: agent
why:
    - observability-ranks.md
    - silence-is-the-default.md
---

# Prefer Dissolving an Invariant to Checking It

Given a choice between adding a detector and changing the representation
so the violating state cannot arise, take the representation change. A
dissolved invariant is not a requirement that is well enforced; it is a
requirement that no longer exists, and so cannot be skipped, forgotten,
disabled in a hurry, or left behind by a refactor that nobody
re-verifies.

The argument is about what survives restructuring. A check is a second
artifact that has to keep agreeing with a first; every edit to either is
an opportunity for them to part company, and the parting is itself silent
(`silence-is-the-default.md`). A representation carries its invariant in
one place, so there is nothing left to fall out of step.

The declined alternative is "add a check and a note in the README." That
buys rank `checked` for the cost of two artifacts and a habit. It is the
right buy sometimes -- see `price-of-dissolving.md` -- but it is the
default answer only because it is the cheaper edit today, which is not a
reason.
