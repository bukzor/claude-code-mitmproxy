# monitoring/ — the checks, as a suite

Every property in a `claude_mitmproxy.check_*` module, asserted against the real
data on disk: masks, promoted fixtures, captures, patch rules. One command, each
property isolated, so one failure no longer hides the rest.

**A failure here is triage, not a broken build.** These read data that changes
without anyone editing code -- upstream rewrites a prompt, a session captures a
new shape, a mask stops matching. Red means go look at the data; the answer is
often to promote a fixture, not to change anything under version control.
`CLAUDE.kb/patch-failure-triage.md` is the companion procedure.

That is the split with `tests/`: there, a failure is always a code defect,
because the test built its own inputs. Here the inputs are whatever is really
on disk. Nothing in this directory may seed data -- if a check needs data that
isn't there it skips (`REQUIRES` in `test_checks.py`), because asserting about
absent data proves nothing.

## Nothing check-specific lives here

`test_checks.py` parametrizes over `CHECKS × PREDICATES`; there is no per-check
test file and nothing to add when a check grows a property. A property is a
function in a check module's `PREDICATES` tuple, next to the data it reads, and
it shows up here as a test on the next run. That is what makes the hand-run
command and this suite unable to disagree about what healthy means: they call
the same function object. See `verdict.py` for the normal form.

The one thing this directory owns is skip policy. A check asserts when its data
is missing -- an absent patch dir is a broken environment, and a command that
shrugged at one would measure a clean zero-strip run -- but a checkout that has
never run the proxy is not broken, it is empty. `REQUIRES` is where that
difference is written down.
