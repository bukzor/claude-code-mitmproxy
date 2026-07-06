# Pyright LSP lifecycle (Claude Code built-in)

Claude Code's built-in Python LSP runs `.venv/bin/pyright-langserver`
(provided here via the `basedpyright-as-pyright` dep) as a direct child of
the `claude` process, and `[tool.pyright] venvPath` in `pyproject.toml`
points import resolution at `.venv`.

Gotchas, observed 2026-07-05:

- The langserver snapshots the environment's installed packages at startup.
  After `uv add`, new imports still report `reportMissingImports` until the
  server restarts.
- Never kill the langserver process by hand: the plugin keeps the dead
  handle and every LSP call fails with the (misleading) error
  "Cannot send request ... server is running" until the whole Claude Code
  session restarts. No in-session recovery exists.
- So: after adding a dependency, restart the session to pick it up.
