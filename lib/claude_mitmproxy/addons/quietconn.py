"""Silence per-connection lifecycle chatter (client/server connect/disconnect).

mitmproxy logs every connection event at INFO from `mitmproxy.proxy.server`
(proxy/server.py), 4-6 lines per API call -- enough to bury what this proxy
is loud about on purpose: new captures, patch incidents, reloads. Capping
that one logger at WARNING keeps its warnings and errors printing.

Runs at module level like `reload.py`: there is no flow to hook, and
re-execution on edit is idempotent.
"""
import logging

logging.getLogger("mitmproxy.proxy.server").setLevel(logging.WARNING)
