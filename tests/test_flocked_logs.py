"""Reopening a flocked log fd is idempotent across a reload.

Both reload paths -- mitmproxy re-executing an edited `-s` addon, and
`reload.py` re-executing a library module -- run this code again in a process
that may already hold the fd and its lock. Module-level state cannot survive
either (a fresh namespace in one case, a clobbered `__dict__` in the other), so
the fd is recovered from `/proc/self/fd` instead: an exhaustive scan of our own
fds is what makes a leftover lock distinguishable from a foreign one, with no
`/proc/locks` lookup needed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from claude_mitmproxy import flocked_logs


def flock_in_subprocess(path: Path) -> subprocess.Popen:
    """A separate process holding an exclusive flock on path until killed."""
    child = subprocess.Popen(
        [sys.executable, "-c",
         "import fcntl, os, sys;"
         "fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT);"
         "fcntl.flock(fd, fcntl.LOCK_EX);"
         "print('locked', flush=True);"
         "sys.stdin.read()",
         str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    assert child.stdout is not None
    assert child.stdout.readline().strip() == "locked"
    return child


def foreign_flock_fails(path: Path) -> bool:
    """Whether a separate process is refused an exclusive flock on path."""
    probe = subprocess.run(
        [sys.executable, "-c",
         "import fcntl, os, sys;"
         "fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT);"
         "exec('try:\\n fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\\n"
         "except BlockingIOError:\\n sys.exit(9)')",
         str(path)],
    )
    return probe.returncode == 9


def test_returns_an_fd_holding_an_exclusive_lock(tmp_path):
    fd = flocked_logs.reopen_flocked_file(tmp_path / "events.log")
    assert foreign_flock_fails(tmp_path / "events.log")
    os.close(fd)


def test_second_call_reuses_our_fd_rather_than_self_conflicting(tmp_path):
    first = flocked_logs.reopen_flocked_file(tmp_path / "events.log")
    second = flocked_logs.reopen_flocked_file(tmp_path / "events.log")
    assert first == second, (first, second)
    os.close(first)


def test_lock_is_released_once_the_fd_is_closed(tmp_path):
    os.close(flocked_logs.reopen_flocked_file(tmp_path / "events.log"))
    assert not foreign_flock_fails(tmp_path / "events.log")


def test_foreign_holder_is_reported_rather_than_silently_shared(tmp_path):
    child = flock_in_subprocess(tmp_path / "events.log")
    try:
        with pytest.raises(BlockingIOError) as caught:
            flocked_logs.reopen_flocked_file(tmp_path / "events.log")
        assert "events.log" in str(caught.value), caught.value
    finally:
        child.kill()
        child.wait()


def test_log_fd_is_todays_shard(tmp_path):
    base = tmp_path / "system-prompt"
    fd = flocked_logs.reopen_log_file(base, when=date(2026, 8, 31))
    assert os.readlink(f"/proc/self/fd/{fd}") == str(
        tmp_path / "system-prompt.2026-08-31.log"
    )
    os.close(fd)


def test_yesterdays_shard_is_released_when_today_is_opened(tmp_path):
    base = tmp_path / "system-prompt"
    yesterday = tmp_path / "system-prompt.2026-08-30.log"
    flocked_logs.reopen_log_file(base, when=date(2026, 8, 30))
    flocked_logs.reopen_log_file(base, when=date(2026, 8, 31))
    # Not the fd number: os.open recycles the one just closed, so identity
    # proves nothing. The contract is that nothing of ours still targets the
    # old shard, and that its lock is therefore gone.
    assert str(yesterday) not in flocked_logs.self_fd_targets().values()
    assert not foreign_flock_fails(yesterday)


def test_unrelated_log_in_the_same_directory_is_left_alone(tmp_path):
    sibling = tmp_path / "subagent-prompt.2026-08-30.log"
    flocked_logs.reopen_log_file(tmp_path / "subagent-prompt", when=date(2026, 8, 30))
    flocked_logs.reopen_log_file(tmp_path / "system-prompt", when=date(2026, 8, 31))
    # Again not the fd number, which os.open recycles: the sibling's lock is
    # what must survive rotating a different log in the same directory.
    assert str(sibling) in flocked_logs.self_fd_targets().values()
    assert foreign_flock_fails(sibling)
