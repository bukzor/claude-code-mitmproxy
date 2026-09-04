"""`save_prompt` says whether it wrote: the raw path on a first sighting, None
on a repeat. The addon's capture event is gated on exactly that answer, so a
function that writes but answers None captures silently -- which is how every
live capture from 2026-08-31 to 2026-09-04 went unannounced.
"""

from __future__ import annotations

from claude_mitmproxy import prompt_capture
from claude_mitmproxy import prompt_location


def body(tag: str) -> str:
    return f"{prompt_location.BODY_MARKER}\n\ntest body {tag}\n"


def masked_sibling(raw):
    return raw.with_name(f"{raw.name.removesuffix('.raw.md')}.md")


def test_first_sighting_returns_the_raw_path(tmp_path):
    saved = prompt_capture.save_prompt(body("a"), "0.0.1", "test", tmp_path)
    assert saved is not None
    assert saved.parent == tmp_path
    assert saved.name.endswith(".raw.md")
    assert saved.read_text() == body("a")
    assert masked_sibling(saved).exists()


def test_repeat_sighting_returns_none_and_writes_nothing(tmp_path):
    first = prompt_capture.save_prompt(body("b"), "0.0.1", "test", tmp_path)
    assert first is not None
    # Dedup is by masked content, so a new release or model of the same text
    # is a repeat, not a new capture.
    assert prompt_capture.save_prompt(body("b"), "0.0.2", "other", tmp_path) is None
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        [first.name, masked_sibling(first).name]
    )
