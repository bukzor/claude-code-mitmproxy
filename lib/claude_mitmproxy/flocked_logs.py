"""Flocked, day-sharded log fds that survive a reload.

Every entry point here is idempotent against a process that already holds what
it is asked to open, because both reload paths re-run this code in place: an
edited `-s` addon is re-executed into a fresh namespace, and `touch reload.py`
re-executes a library module into its existing `__dict__`. Neither leaves a
usable module-level reference behind, so the fd is recovered from
`/proc/self/fd` rather than remembered.
"""

from __future__ import annotations

import errno
import fcntl
import os
from datetime import date
from pathlib import Path

SELF_FD_DIR = Path("/proc/self/fd")
SUFFIX = ".log"


def fd_target(entry: Path) -> str | None:
    """What this `/proc/self/fd` entry points at, or None once it points at
    nothing.

    An fd closed between the listing and the readlink has no target, so None is
    the answer rather than a failure -- and there is always at least one, the
    listing's own directory fd, which `os.listdir` closes before this runs.
    Anything else propagates: these callers reason from an *exhaustive* view of
    our own fds, and a scan that quietly thinned itself would leave that
    reasoning intact and wrong.
    """
    try:
        return os.readlink(entry)
    except FileNotFoundError:
        return None


def self_fd_targets() -> dict[int, str]:
    """What each of our open fds points at, by fd number.

    A deleted file reads back as "<path> (deleted)" and so matches nothing
    here, which is correct: a lock on an unlinked inode cannot conflict with a
    fresh open of that name.
    """
    return {
        int(entry.name): target
        for entry in SELF_FD_DIR.iterdir()
        if (target := fd_target(entry)) is not None
    }


def shard_path(base: Path, when: date) -> Path:
    """The shard of log `base` covering `when`.

    Date last, so the taxonomy sorts before it and one glob spans a log's whole
    history; `.log` stays the suffix, which is what keeps `compress_traffic`'s
    archive-beside-capture naming working unchanged.
    """
    return base.with_name(f"{base.name}.{when:%Y-%m-%d}{SUFFIX}")


def holds_lock(fd: int) -> bool:
    """Whether `fd` holds this file's exclusive flock, taking it when it is free.

    There is no way to ask, so it is asked by trying, and both outcomes are
    answers rather than events: re-locking the fd that already holds the lock
    succeeds as a no-op, and a refusal means some *other* open file description
    holds it -- a second fd conflicts even within one process, because the lock
    belongs to the description.
    """
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def reopen_flocked_file(path: Path) -> int:
    """An fd on `path` holding an exclusive flock; ours if we already hold one.

    Trying each of our own fds in turn both finds the holder and proves, when
    none succeeds, that any remaining holder is a different process -- the scan
    is exhaustive over our open descriptions, so nothing of ours is left to be
    the holder. That is why telling a leaked reload apart from a second proxy
    needs no `/proc/locks`. A description of ours that does not hold the lock is
    skipped rather than trusted: the answer is which fd holds it, and one that
    does not is simply not that fd.

    Raises BlockingIOError, naming the path, when another process holds it. The
    caller decides whether that is fatal; here it is only reported.
    """
    targets = self_fd_targets()
    for fd in (fd for fd, target in targets.items() if target == str(path)):
        if holds_lock(fd):
            return fd
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    if not holds_lock(fd):
        os.close(fd)
        raise BlockingIOError(errno.EWOULDBLOCK, "held by another process", str(path))
    return fd


def reopen_log_file(base: Path, when: date) -> int:
    """A flocked fd on log `base`'s shard for `when`, closing ours on its others.

    Rotation carries no state: the shard is recomputed per call and a stale fd
    is found by scanning, so there is no cached path that can fall out of sync
    with the open fd -- the desync that took `flow2jsonl` dark for hours
    (design/040-design.kb/ease-of-operation.kb/rotation-self-heals.md) is not
    representable here.

    Only shards of this log are touched: a sibling log in the same directory
    keeps its fd and its lock.
    """
    current = shard_path(base, when)
    prefix = f"{base}."
    for fd, target in self_fd_targets().items():
        if target.startswith(prefix) and target.endswith(SUFFIX) and target != str(current):
            os.close(fd)
    current.parent.mkdir(parents=True, exist_ok=True)
    return reopen_flocked_file(current)
