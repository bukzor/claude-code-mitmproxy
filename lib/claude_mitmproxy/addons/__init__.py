"""The modules mitmproxy loads with `-s`, and nothing else.

Membership here is a fact about `proxy.sh`, not a topic: every file in this
directory appears on a `-s` line, every `-s` line names a file here. That is
what makes an addon recognizable at a glance, which flat naming could not do
-- `syscapture.py` and `prompt_capture.py` read alike and are nothing alike.

The rule that keeps it true in both directions: **nothing outside this
directory may import `claude_mitmproxy.addons`.** An addon holds mitmproxy
hooks and delegates immediately; whatever an offline caller wants is in the
library module it delegates to, which is importable without mitmproxy
installed. `addons/reload.py` asserts this -- a check that reached in here
would put the two kinds back in one bag, one level down.

Nothing imports this package, so this file exists only to say so. mitmproxy
path-loads each addon as `__mitmproxy_script__.<stem>`, which is why the
imports inside them are absolute (`CLAUDE.kb/reloading-a-live-proxy.md`).
"""
