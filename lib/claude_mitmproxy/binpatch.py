#!/usr/bin/env python3
"""Byte-patch the installed Claude Code binary to undo compiled-in behavior.

Some Claude Code behavior is baked into the CLI with no setting, env var, or
hook to change it, and it never crosses the wire -- so the proxy patches
(prompt_patches.py, tool_patches.py) cannot reach it. This does, by
substituting bytes in the on-disk binary. Every substitution is equal-length,
so file offsets and the executable's internal structure are untouched; the
bun-compiled binary embeds the bundle twice (JS source + JSC bytecode
constants), so each patch expects two hits.

Runs as a SessionStart hook (CLAUDE.kb/binpatch-and-its-session-hook.md). The
already-running session keeps the old code mapped from memory -- os.replace
swaps a fresh inode in without touching the busy one -- so a just-applied patch
means "restart to apply", surfaced on stderr with exit 2 (SessionStart shows
hook stderr to the user, not to the model, and proceeds). After each Claude
Code auto-update installs a fresh unpatched binary, the next session's hook
re-applies automatically.

Exit codes: 0 already patched (silent); 2 just patched (restart to apply);
1 drift -- a patch's byte pattern no longer appears the expected number of
times, so nothing was written and the guarded behavior may be live again.
"""

from __future__ import annotations

import mmap
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TARGET = Path.home() / ".local/bin/claude"


@dataclass(frozen=True)
class Patch:
    name: str
    search: bytes
    replace: bytes
    expect: int

    def __post_init__(self):
        assert len(self.search) == len(self.replace), (
            self.name,
            self.search,
            self.replace,
        )
        assert self.search != self.replace, self.name


class Drift(Exception):
    """A patch's target no longer appears `expect` times pristine nor patched,
    so the binary changed shape upstream and the substitution is unsafe."""

    def __init__(self, patch: Patch, pristine: int, patched: int):
        self.patch = patch
        self.pristine = pristine
        self.patched = patched
        super().__init__(
            f"{patch.name}: expected {patch.expect} matches, found {pristine}"
            f" pristine / {patched} patched -- upstream changed; re-derive"
        )


# Write.validateInput rejects a subagent writing a basename matching
# /^(REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$/i -- inverting a kb workflow where
# a findings.md on disk is the deliverable. A literal Q appended past the
# extension anchor keeps the regex valid but unable to match any real filename.
PATCHES: tuple[Patch, ...] = (
    Patch(
        name="subagent-md-report-guard",
        search=rb"REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$",
        replace=rb"REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.mdQ",
        expect=2,
    ),
)


def count(haystack: mmap.mmap | bytes, sub: bytes) -> int:
    """Non-overlapping occurrences of sub, via find so one implementation
    serves both a bytes blob and a read-only mmap of the unloaded file."""
    n = 0
    i = haystack.find(sub)
    while i != -1:
        n += 1
        i = haystack.find(sub, i + len(sub))
    return n


def classify(haystack: mmap.mmap | bytes, patch: Patch) -> str:
    """'patched' or 'pristine'; raise Drift when neither count is `expect`."""
    pristine = count(haystack, patch.search)
    patched = count(haystack, patch.replace)
    if pristine == 0 and patched == patch.expect:
        return "patched"
    elif pristine == patch.expect and patched == 0:
        return "pristine"
    else:
        raise Drift(patch, pristine, patched)


def apply(blob: bytes, patches: tuple[Patch, ...]) -> bytes:
    for patch in patches:
        blob = blob.replace(patch.search, patch.replace)
    return blob


def write_atomic(target: Path, blob: bytes):
    """Replace target via a same-directory temp file + rename, so a process
    executing the old binary keeps its inode and never meets a half-written
    one (no ETXTBSY -- we never write the busy inode, we swap a new one in)."""
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=target.name + ".binpatch.")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(blob)
        os.chmod(tmp, target.stat().st_mode)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET).resolve()
    with open(target, "rb") as f, mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ) as mm:
        try:
            states = {patch.name: classify(mm, patch) for patch in PATCHES}
        except Drift as drift:
            print(f"binpatch: {drift} (see {__file__})", file=sys.stderr)
            return 1
    stale = tuple(patch for patch in PATCHES if states[patch.name] == "pristine")
    if not stale:
        return 0
    write_atomic(target, apply(target.read_bytes(), stale))
    print(
        f"binpatch: patched {target}"
        f" ({', '.join(patch.name for patch in stale)}). This session still"
        " runs the un-patched binary from memory -- restart Claude Code to apply.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
