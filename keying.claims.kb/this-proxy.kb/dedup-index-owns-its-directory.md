---
label: DIR_OWNERSHIP
standing: agent
why:
    - ../derivation.kb/memo-coverage-is-per-component.md
    - ../store.kb/name-by-identity-dedup-by-class.md
---

# The Dedup Index Is Stale-Proof in the Masks and Owner-Protected in the Files

`prompt_capture.py` memoizes the set of masked digests under the mask set
object itself. `WHOLE_INPUT` therefore applies to that component exactly:
`incidents.masks()` is re-read per request and the templates are
NamedTuples, so a changed `masks.d/` yields a value that cannot compare
equal to the cached one, and the index rebuilds with no command, no
fingerprint, and no mtime. That part is dissolved, not checked.

The input has a second component and the key does not cover it: the
directory's contents. `load_masked_digests` walks `*.raw.md` once and then
trusts its own set. A capture appearing by any route other than
`save_prompt` is invisible until the mask set changes or the process
restarts.

Per `COVERAGE` that is admissible only against an ownership argument, so
here it is, stated as the premise it is: **the live proxy process is the
sole writer of `log/prompt-captures/`, and it updates the set on every
write.** The argument holds for the routes that exist -- the directory is
gitignored, written by one addon, and read by tooling that never adds to
it. It fails for a human dropping a file in mid-run, and for a second
proxy process against the same directory.

The consequence of the failure is mild and bounded, which is why the
ownership argument is accepted rather than engineered away: a missed
capture is captured again under its own name, costing one duplicate file
whose content differs only in session noise. Nothing is lost and nothing
is corrupted.

**What would kill it.** A second writer -- a migration script, a recovery
procedure, a second proxy -- run against a live directory. The fix then is
not a fingerprint but dropping the memo: the rebuild is a directory walk.
