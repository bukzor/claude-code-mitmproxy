# monitoring/ — the checks, as a suite

Every property in a `claude_mitmproxy.check_*` module, asserted against the real
data on disk: masks, promoted fixtures, captures, patch rules. One command, each
property isolated, so one failure no longer hides the rest.

**A failure here is usually triage, not a broken build.** Most of these read
data that changes without anyone editing code -- upstream rewrites a prompt, a
session captures a new shape, a mask stops matching. Red means go look at the
data; the answer is often to promote a fixture, not to change anything under
version control. `CLAUDE.kb/patch-failure-triage.md` is the companion
procedure.

The correspondence checks are the other kind, and which kind a check is
follows from what it reads rather than from a list kept here. If every input
is version-controlled in this repo and changes only when a human edits it,
then nothing upstream can turn the check red: red is a defect in the commit
that caused it, and `--no-verify` suppresses it rather than deferring it. If
any input is written by upstream, by the proxy, or by an automated fixture
promotion, red may be drift and triage is the right reading. `REQUIRES` in
`test_checks.py` already draws half of that line, naming the checks whose
inputs are not version-controlled at all.

That is the split with `tests/`: there, a failure is always a code defect,
because the test built its own inputs. Here the inputs are whatever is really
on disk. Nothing in this directory may seed data -- if a check needs data that
isn't there it skips (`REQUIRES` in `test_checks.py`), because asserting about
absent data proves nothing.

## Nothing check-specific lives here

`test_checks.py` parametrizes over `CHECKS × PREDICATES`, where `CHECKS` is
`check_verdict.all_checks()` -- the check modules on disk, not a list kept
here. So there is no per-check test file and nothing to add when a check grows
a property, nor when the repo grows a check. A property is a function in a
check module's `PREDICATES` tuple, next to the data it reads, and it shows up
here as a test on the next run. That is what makes the hand-run command and
this suite unable to disagree about what healthy means: they call the same
function object. See `check_verdict.py` for the normal form, and
`tests/test_all_checks.py` for what holds discovery and that form together.

The one thing this directory owns is skip policy. A check asserts when its data
is missing -- an absent patch dir is a broken environment, and a command that
shrugged at one would measure a clean zero-strip run -- but a checkout that has
never run the proxy is not broken, it is empty. `REQUIRES` is where that
difference is written down.
