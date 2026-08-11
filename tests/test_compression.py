"""compress_traffic.py deletes originals; this is the detector for the day it
deletes one it should have kept.

Every other guard in this repo protects data upstream will send again. This one
protects the only copy, and nothing at proxy time notices a sweep that quietly
took a shard it should have left alone -- the shard is simply gone. So the
interesting property is not that it compresses, but what it refuses to touch,
and what survives when a compression goes wrong.

One sweep runs over a throwaway directory holding one capture of every case it
must tell apart -- finished, unverifiable, held open by a live process, dated
today -- and the archives are read back with plain `zstd`, never with the
comparator under test.
"""
from __future__ import annotations

import fcntl
import os
import subprocess
import time
from datetime import date
from pathlib import Path
from typing import NamedTuple

import pytest

import compress_traffic

LINE = '{"phase":"request","data":{"headers":[["host","api.anthropic.com"]]}}\n'
BODY = LINE * 20000
AGED = time.time() - 5 * 86400


class Swept(NamedTuple):
    """The seeded captures, after one sweep has run over them."""

    unverifiable: Path
    finished: Path
    open_now: Path
    todays: Path
    exit: SystemExit


def seed(traffic_dir: Path, name: str, aged: bool) -> Path:
    """One capture. `aged` backdates the mtime, which is the whole of what the
    sweep reads to decide a shard is finished."""
    path = traffic_dir / name
    path.write_text(BODY)
    if aged:
        os.utime(path, (AGED, AGED))
    return path


def restored(archive: Path) -> str:
    """What the archive holds, read back independently of the comparator these
    tests are checking."""
    zstd = subprocess.run(
        ["zstd", "-dc", "--long", str(archive)], stdout=subprocess.PIPE, check=True
    )
    return zstd.stdout.decode()


@pytest.fixture
def swept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Swept:
    """One sweep, with the round-trip check rigged to fail on the capture that
    sorts first -- so anything archived afterwards proves the run continued."""
    unverifiable = seed(tmp_path, "2026-08-01.jsonl", aged=True)
    finished = seed(tmp_path, "2026-08-02.jsonl", aged=True)
    open_now = seed(tmp_path, "2026-08-03.jsonl", aged=True)
    todays = seed(tmp_path, f"{date.today()}.jsonl", aged=False)

    honest = compress_traffic.matches_decompressed
    monkeypatch.setattr(compress_traffic, "TRAFFIC_DIR", tmp_path)
    monkeypatch.setattr(compress_traffic, "LOCK_PATH", tmp_path / ".compress.lock")
    # The failure below is provoked, so it must not reach the real incident
    # store: None is the seam check_patches uses for the same reason.
    monkeypatch.setattr(compress_traffic, "CAPTURE_DIR", None)
    monkeypatch.setattr(
        compress_traffic,
        "matches_decompressed",
        lambda archive, original: (
            False if original == unverifiable else honest(archive, original)
        ),
    )

    with open_now.open("rb"):  # this very process is the "running process"
        with pytest.raises(SystemExit) as exit:
            compress_traffic.main([])
    return Swept(unverifiable, finished, open_now, todays, exit.value)


def test_finished_capture_is_archived(swept: Swept):
    """It sorts after the rigged failure, so this also proves the sweep does
    not stop at one capture it cannot archive."""
    assert compress_traffic.archive_of(swept.finished).exists()


def test_archive_holds_the_original_bytes(swept: Swept):
    assert restored(compress_traffic.archive_of(swept.finished)) == BODY


def test_archived_original_is_removed(swept: Swept):
    assert not swept.finished.exists()


def test_unverifiable_archive_is_not_published(swept: Swept):
    assert not compress_traffic.archive_of(swept.unverifiable).exists()


def test_unverifiable_archive_stays_a_part_file(swept: Swept):
    """What a stray .part on disk means: a run that could not vouch for its
    archive. The retry overwrites it, so it needs no cleaning up."""
    archive = compress_traffic.archive_of(swept.unverifiable)
    assert archive.with_name(archive.name + ".part").exists()


def test_unverifiable_capture_is_kept_whole(swept: Swept):
    assert swept.unverifiable.read_text() == BODY


def test_failure_reaches_the_exit_status(swept: Swept):
    assert "1 capture" in str(swept.exit)


def test_open_capture_is_untouched(swept: Swept):
    assert swept.open_now.read_text() == BODY
    assert not compress_traffic.archive_of(swept.open_now).exists()


def test_todays_capture_is_untouched(swept: Swept):
    """Not held open by anyone here: today's shard is off limits even with the
    proxy stopped, because a restart appends to it."""
    assert swept.todays.read_text() == BODY
    assert not compress_traffic.archive_of(swept.todays).exists()


def test_a_second_run_defers_to_the_lock_holder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Two runs writing one archive would both fail the round-trip check --
    sparing the originals, but leaving a .part named for a capture that is
    still there, and a second run doing nothing is cheaper than reasoning
    about that."""
    capture = seed(tmp_path, "2026-08-01.jsonl", aged=True)
    lock_path = tmp_path / ".compress.lock"
    monkeypatch.setattr(compress_traffic, "TRAFFIC_DIR", tmp_path)
    monkeypatch.setattr(compress_traffic, "LOCK_PATH", lock_path)

    held = lock_path.open("w")
    fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        compress_traffic.main([])
    finally:
        held.close()

    assert capture.read_text() == BODY
    assert not compress_traffic.archive_of(capture).exists()
