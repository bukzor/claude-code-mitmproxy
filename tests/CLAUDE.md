# tests/ — pytest suite

Belongs here: behavior that can be checked against fixtures the test builds
itself. Run with `.venv/bin/pytest` — plain, not `uv run`, which re-syncs
`.venv` while the live proxy is running out of it.

Does not belong: validation of the real data on disk — captures, masks, patch
templates, the strip floors. Those are the `check_*.py` modules, run by hand
against whatever is actually there, with no fixed expected output. Test the
machinery here; check the data there.

> [!DRAFT] agent-authored 2026-09-17, vetoable — one standing exception.
>
> `test_message_patches.py` loads the live rules from
> `message_patches.PATCHES_DIR`. The reason the split exists does not reach
> that locus: the line above assumes real-data validation has no fixed
> expected output, and here it does — the two upstream steer bodies are
> carried in the test verbatim, so a miss is a definite failure rather than
> upstream churn to triage. It has no captured fixtures to test against
> either. The cost is real and accepted: that file needs the operator's
> `~/.config/claude-mitmproxy/system-message.d/` to collect at all.

Import the package, not its contents (`from claude_mitmproxy import
prompt_patches`) — the form `reload.py` requires of the addons themselves.
`pythonpath = ["lib"]` is what makes it resolve without an install.

A test that provokes a failure in code that reports incidents must set that
module's `CAPTURE_DIR` to None, or it files a real incident for someone to
triage. `incidents.py` documents the seam; `test_compression.py` uses it.
