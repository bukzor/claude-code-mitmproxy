---
why:
  - earned-silence
  - decoupled-from-the-cli
---

# Exact-compare tool stubs

`toolpatch.py` deliberately does not reuse the template patch model.
Tool descriptions are replaced whole -- the stub is self-contained, so
there is no "precise text to replace" inside a body, only "which
reviewed upstream wording is this?" That question wants byte-equality
against an accepted set (`upstream.md` / `upstream.d/*.md`), not
placeholder templates: wordings vary as discrete concurrent variants
(interface and model family, not just cc_version), and any unreviewed
byte is exactly what the tripwire must catch.

On drift the stub is still applied -- availability over freshness; the
live text is captured loudly once so review can absorb it into
`upstream.d/` or the stub. Guidance stripped from a description must
survive somewhere lazy-loaded (e.g.
`~/.claude/must-read.kb/before/using-claude-code-tool/Monitor.md`);
the stub carries a pointer.
