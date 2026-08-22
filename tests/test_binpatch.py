"""binpatch classifies and rewrites without a real 342 MB binary in hand.

The failure this guards is a corrupted executable, so the length-preserving
substitution and the drift check -- all that stands between a changed upstream
and a wrong-count write -- are pinned here on a synthetic blob.
"""

from __future__ import annotations

import pytest

from claude_mitmproxy import binpatch

PATCH = binpatch.Patch("t", b"AAAA", b"AABB", expect=2)
PRISTINE = b"xxAAAAyyAAAAzz"  # exactly two hits
PATCHED = PRISTINE.replace(b"AAAA", b"AABB")


def test_unequal_length_is_rejected():
    with pytest.raises(AssertionError):
        binpatch.Patch("bad", b"AAAA", b"BBB", expect=1)


def test_count_is_non_overlapping():
    assert binpatch.count(b"AAAAA", b"AA") == 2  # positions 0 and 2, not 4


def test_classify_reads_both_states():
    assert binpatch.classify(PRISTINE, PATCH) == "pristine"
    assert binpatch.classify(PATCHED, PATCH) == "patched"


def test_classify_drifts_on_unexpected_count():
    with pytest.raises(binpatch.Drift):
        binpatch.classify(b"xxAAAAzz", PATCH)  # one hit, expect two


def test_apply_is_length_preserving_and_lands_patched():
    once = binpatch.apply(PRISTINE, (PATCH,))
    assert once == PATCHED
    assert len(once) == len(PRISTINE)
    assert binpatch.classify(once, PATCH) == "patched"


def test_real_patches_are_well_formed():
    for patch in binpatch.PATCHES:
        assert len(patch.search) == len(patch.replace)
        assert patch.expect >= 1


def test_write_atomic_swaps_the_inode(tmp_path):
    target = tmp_path / "bin"
    target.write_bytes(b"old")
    before = target.stat().st_ino
    binpatch.write_atomic(target, b"new")
    assert target.read_bytes() == b"new"
    assert target.stat().st_ino != before  # replaced, not overwritten in place
