"""Prompt-shape classification, shared by the live strip-rate tripwire
(syspatch.py) and the capture inventory (survey_captures.py).

Anthropic serves structurally distinct system-prompt shapes concurrently,
correlated with model class; each is named for a heading unique to it.
Markers are ordered: first hit wins, so more-specific headings (the
post-split harness variants) precede the generic `# Harness`."""
from __future__ import annotations

SHAPE_MARKERS = (
    ("# Communicating with the user", "harness-fable"),
    ("# Delivering work", "harness-opus"),
    ("# Harness", "harness"),  # pre-split (< v2.1.221) Fable-class shape
    ("# Doing tasks", "long-form"),
)


def shape_of(text: str) -> str:
    """The known shape name, or `?<first heading>` for an unrecognized
    body -- callers treat the `?` prefix as "no known shape"."""
    for marker, shape in SHAPE_MARKERS:
        if f"\n{marker}\n" in text or text.startswith(f"{marker}\n"):
            return shape
    first_heading = next(
        (line for line in text.splitlines() if line.startswith("#")), "(none)"
    )
    return f"?{first_heading!r}"
