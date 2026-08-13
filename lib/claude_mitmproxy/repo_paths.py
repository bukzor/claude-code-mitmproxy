"""Where the repo is, for the code that lives three directories inside it.

Rule directories (`masks.d/`, `blocks.d/`), fixtures (`system-prompts.kb/`)
and everything generated (`log/`) are anchored to the checkout, not to the
package: they are edited by hand and read by the proxy, and both halves have
to name the same files. One `__file__` here beats nine that each have to be
re-counted whenever the package moves.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOG = ROOT / "log"
