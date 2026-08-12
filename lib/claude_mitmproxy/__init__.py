"""mitmproxy addons and offline tooling for patching Claude Code traffic.

Import submodules as modules, never their contents:
`from claude_mitmproxy import syspatch`, then `syspatch.apply_patches(...)`.
`from claude_mitmproxy.syspatch import apply_patches` copies the reference and
so survives a `reload.py` reload with the old function -- see that module.
Relative imports are out for a different reason: mitmproxy path-loads the
addons as `__mitmproxy_script__.<stem>`, where a leading dot resolves nowhere.
"""
