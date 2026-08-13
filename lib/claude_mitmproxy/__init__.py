"""Offline tooling for patching Claude Code traffic, plus the `addons/` that
run it in a live proxy.

Everything here imports without mitmproxy installed -- everything in
`addons/` does not, and holds nothing but hooks. That split is what lets the
six offline checks exercise the code the proxy runs; `addons/__init__.py`
states the rule that keeps it true.

Import submodules as modules, never their contents -- say
`from claude_mitmproxy import prompt_patches`, then
`prompt_patches.apply_patches(...)`, because the reaching-in form
`from claude_mitmproxy.prompt_patches import apply_patches`
copies the reference and so survives a `reload.py` reload holding the old
function -- see that module. Relative imports are out for a different reason:
mitmproxy path-loads the addons as `__mitmproxy_script__.<stem>`, where a
leading dot resolves nowhere.
"""
