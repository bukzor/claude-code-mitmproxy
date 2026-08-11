#!/usr/bin/env python3
"""Offline validation of compress_traffic.py, which deletes originals.

Every other guard in this repo protects data that upstream will send again.
This one protects the only copy: the sweep unlinks a capture on the strength
of a round-trip comparison, so the interesting question is not whether it
compresses but what it refuses to touch, and what survives when a compression
goes wrong. Nothing at proxy time notices a sweep that quietly took a shard it
should have left alone -- the shard is simply gone. This is the detector.

Seeds a throwaway directory with one capture of every case the sweep must tell
apart -- finished, unarchivable, held open by a live process, dated today --
then reads the results back with plain `zstd -dc`, never with the comparator
under test. The real log/traffic/ is untouched.

Usage: check_compression.py -- exits nonzero on the first missing `ok`. The
sweep's own FAIL and skip lines are expected here: it is being provoked.
"""
from __future__ import annotations

import os
import subprocess
import time
from datetime import date
from pathlib import Path

import compress_traffic

WORK_DIR = Path(__file__).parent / "log" / "check-compression"
LINE = '{"phase":"request","data":{"headers":[["host","api.anthropic.com"]]}}\n'
BODY = LINE * 20000
AGED = time.time() - 5 * 86400


def seed(name: str, aged: bool) -> Path:
    """One capture. `aged` backdates the mtime, which is the whole of what the
    sweep reads to decide a shard is finished."""
    path = WORK_DIR / name
    path.write_text(BODY)
    if aged:
        os.utime(path, (AGED, AGED))
    return path


def sweep(doomed: Path) -> None:
    """Run the sweep against WORK_DIR with `doomed`'s round-trip rigged to
    fail, and require it to say so in its exit status."""
    honest = compress_traffic.matches_decompressed
    compress_traffic.matches_decompressed = lambda archive, original: (
        False if original == doomed else honest(archive, original)
    )
    compress_traffic.TRAFFIC_DIR = WORK_DIR
    compress_traffic.LOCK_PATH = WORK_DIR / ".compress.lock"
    compress_traffic.CAPTURE_DIR = None  # provoked on purpose; not an incident
    try:
        compress_traffic.main()
    except SystemExit as exit:
        assert "1 capture" in str(exit), exit
    else:
        raise AssertionError("rigged round-trip failure exited clean")
    finally:
        compress_traffic.matches_decompressed = honest


def restored(archive: Path) -> str:
    """What the archive actually holds, read back independently of the
    comparator this is checking."""
    zstd = subprocess.run(
        ["zstd", "-dc", "--long", str(archive)], stdout=subprocess.PIPE, check=True
    )
    return zstd.stdout.decode()


def expect(what: str, ok: bool) -> None:
    assert ok, what
    print(f"ok {what}")


def main() -> None:
    if WORK_DIR.exists():
        for stale in sorted(WORK_DIR.iterdir()):
            stale.unlink()
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    doomed = seed("2026-08-01.jsonl", aged=True)
    ordinary = seed("2026-08-02.jsonl", aged=True)
    busy = seed("2026-08-03.jsonl", aged=True)
    todays = seed(f"{date.today()}.jsonl", aged=False)
    archive = compress_traffic.archive_of

    with busy.open("rb"):  # this very process is the "running process"
        sweep(doomed)

    expect("finished capture archived", archive(ordinary).exists())
    expect("archive holds the original bytes", restored(archive(ordinary)) == BODY)
    expect("archived original removed", not ordinary.exists())

    expect("unverifiable archive not published", not archive(doomed).exists())
    expect("its capture kept whole", doomed.read_text() == BODY)
    expect("sweep continued past it", not ordinary.exists())

    expect("open capture untouched", busy.read_text() == BODY)
    expect("open capture not archived", not archive(busy).exists())

    expect("today's capture untouched", todays.read_text() == BODY)
    expect("today's capture not archived", not archive(todays).exists())


if __name__ == "__main__":
    main()
