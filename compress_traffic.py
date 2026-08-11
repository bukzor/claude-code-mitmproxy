#!/usr/bin/env python3
"""Compress the day-sharded captures in log/traffic, losslessly, in place.

A retention measure, not a reclamation one. These captures are the most
compressible data this project produces: every turn resends the same system
prompt and the whole conversation prefix, which long-range matching collapses
into back-references. Measured on 200 MiB samples:

    zstd -3           13.1x on .jsonl, 10.2x on .flow
    zstd -19 --long   57x   on .jsonl

So the answer to "the captures are eating the disk" is to keep every byte,
compressed, rather than to set a retention window. Level 16 is the default
because it sits near the -19 ratio at a fraction of the cost.

Reading one back: `zstd -dc --long log/traffic/2026-08-09.jsonl.zst | jq ...`.
flow2jsonl.sh and jsonl2sysprompt.sh take a path and know nothing about .zst,
so decompress to a temp file before handing one to them.

WARNING: these captures store request headers verbatim, including
`Authorization: Bearer sk-ant-...`, and the .zst inherits every one. Never
sync, commit, or attach this directory.
"""
from __future__ import annotations

import fcntl
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

TRAFFIC_DIR = Path(__file__).resolve().parent / "log" / "traffic"
LOCK_PATH = TRAFFIC_DIR / ".compress.lock"
SUFFIXES = (".jsonl", ".flow")
DEFAULT_LEVEL = 16
CHUNK_BYTES = 1 << 20


def human(size: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TiB"


def compressible(traffic_dir: Path) -> list[Path]:
    """Finished captures with no archive beside them yet, oldest shard first.

    A shard written today is not finished even when no process holds it: the
    proxy may be stopped at this instant and appending again in a minute. Its
    archive would then sit beside a fresh, growing file of the same name, and
    every later run would skip that name as already done.
    """
    today = date.today()
    return sorted(
        path
        for path in traffic_dir.rglob("*")
        if path.suffix in SUFFIXES
        and path.is_file()
        and datetime.fromtimestamp(path.stat().st_mtime).date() < today
        and not archive_of(path).exists()
    )


def archive_of(capture: Path) -> Path:
    return capture.with_name(capture.name + ".zst")


def held_open() -> set[Path]:
    """Files currently open by any process this user can see.

    mitmproxy appends to the current day's shard for as long as the proxy
    runs. Compressing under a live writer would archive a prefix and then
    delete the file that writer still holds, silently losing every record
    written afterwards -- no error, no short read, just a day that ends early.
    """
    open_paths: set[Path] = set()
    for fd_dir in Path("/proc").glob("[0-9]*/fd"):
        try:
            links = list(fd_dir.iterdir())
        except (PermissionError, FileNotFoundError):
            continue  # another user's process, or one that exited mid-scan
        open_paths.update(link.resolve() for link in links)
    return open_paths


def matches_decompressed(archive: Path, original: Path) -> bool:
    """Whether archive decompresses to exactly original's bytes.

    Stronger than `zstd -t`, deliberately: a checksum test proves the frame is
    intact, not that it holds *this* file. There is one copy of this data and
    the caller deletes it on the strength of this answer.
    """
    zstd = subprocess.Popen(
        ["zstd", "-dc", "--long", str(archive)], stdout=subprocess.PIPE
    )
    assert zstd.stdout is not None
    try:
        with original.open("rb") as source:
            while True:
                decompressed = zstd.stdout.read(CHUNK_BYTES)
                if decompressed != source.read(CHUNK_BYTES):
                    return False
                if not decompressed:
                    return zstd.wait() == 0
    finally:
        zstd.stdout.close()
        zstd.kill()
        zstd.wait()


def replace_with_archive(capture: Path, level: int) -> tuple[int, int]:
    """Compress capture in place; returns its size before and after.

    The original is removed only once its archive has been read back and
    compared against it in full. Until then the archive is a .part: a killed
    run must not leave a truncated .zst, which is indistinguishable from a
    finished one to the next run and would retire the capture unread.
    """
    before = capture.stat().st_size
    archive = archive_of(capture)
    partial = archive.with_name(archive.name + ".part")
    subprocess.run(
        # -f to overwrite the .part an earlier interrupted run left behind
        ["zstd", f"-{level}", "-T0", "--long", "-q", "-f", "-o", str(partial), str(capture)],
        check=True,
    )
    assert matches_decompressed(partial, capture), (partial, capture)
    partial.replace(archive)
    capture.unlink()
    return before, archive.stat().st_size


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv[1:]
    level = int(args[0]) if args else DEFAULT_LEVEL

    # flow2jsonl.py fires one of these per shard it opens, so a hand-run can
    # collide with it. Both would write the same .zst, and the round-trip check
    # would then reject an interleaved archive for both -- sparing the
    # originals, but leaving a corrupt .zst that makes every later run skip
    # that day as already done.
    lock = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another run holds the lock; leaving it to that one", file=sys.stderr)
        return

    busy = held_open()
    total_before = total_after = 0
    for capture in compressible(TRAFFIC_DIR):
        size = capture.stat().st_size
        if capture in busy:
            print(f"skip {capture.name}: open by a running process", flush=True)
        elif dry_run:
            print(f"would compress {capture.name} ({human(size)})", flush=True)
        else:
            before, after = replace_with_archive(capture, level)
            total_before += before
            total_after += after
            print(
                f"{capture.name}: {human(before)} -> {human(after)}"
                f" ({before / after:.1f}x)",
                flush=True,
            )

    if total_before:
        print(
            f"total: {human(total_before)} -> {human(total_after)}"
            f" ({total_before / total_after:.1f}x,"
            f" {human(total_before - total_after)} reclaimed)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
