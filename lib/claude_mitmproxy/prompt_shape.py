"""Prompt-shape classification, shared by the live strip-rate tripwire
(prompt_patches.py) and the capture inventory (survey_captures.py).

Anthropic serves structurally distinct system-prompt shapes concurrently,
correlated with model class; each is named for a heading unique to it.
Markers are ordered: first hit wins, so more-specific headings (the
post-split harness variants) precede the generic `# Harness`, and
`# Doing tasks` (unique to the long-form family) precedes
`# Delivering work`, which v2.1.233 sonnet long-form bodies carry too --
only the harness-opus shape lacks `# Doing tasks`."""
from __future__ import annotations

SHAPE_MARKERS = (
    ("# Communicating with the user", "harness-fable"),
    ("# Doing tasks", "long-form"),
    ("# Delivering work", "harness-opus"),
    ("# Harness", "harness"),  # pre-split (< v2.1.221) Fable-class shape
)


# The fixture-name suffix each shape takes (`system-prompts.kb/CLAUDE.md`).
# Beside the markers because both answer "which shape is this": a table
# somewhere else would let a shape exist that nothing can file.
FIXTURE_SUFFIX = {
    "long-form": "",
    "harness": "-harness",
    "harness-fable": "-fable",
    "harness-opus": "-opus",
}
assert FIXTURE_SUFFIX.keys() == {shape for _, shape in SHAPE_MARKERS}, FIXTURE_SUFFIX


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
