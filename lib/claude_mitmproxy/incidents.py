"""Content-addressed capture for addon incidents: shared by syspatch.py's
patch-application issues and any addon hook's uncaught exceptions. Capture is
idempotent on disk, keyed by masked_hash, so a live proxy re-hitting the same
failure on every request logs and writes exactly once.

Also the home of the two digests every store here is keyed by, since masking
defines both: `digest_of` over a body as sent identifies that observation
forever, `masked_hash` identifies its equivalence class under today's
`masks.d/`. Which store uses which, and why they differ:
`design/040-design.kb/content-addressed-capture.md`."""
from __future__ import annotations

import hashlib
import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from claude_mitmproxy import paths
from claude_mitmproxy import templates

# Gitignored; callers pass capture_dir=None to disable capture entirely
# (offline callers like check_patches only want an in-process warning).
CAPTURE_DIR = paths.LOG / "patch-failures"
BODIES_DIRNAME = "_bodies"
ARCHIVE_DIRNAME = "_archive"

# In-repo, unlike the patches under ~/.claude: patches are one operator's
# preferences, but masks define the capture system's identity function, and a
# digest that varied with per-machine state wouldn't be content-addressed.
MASKS_DIR = paths.ROOT / "masks.d"


class Incident(NamedTuple):
    rule: str
    kind: str


def masks() -> tuple[templates.Template, ...]:
    """The compiled mask set, re-read per call exactly as patches are: an edit
    is live on the next request, with no restart, and nothing anywhere holds a
    stale opinion about what a digest should be. Deliberately uncached -- a
    dozen-odd small files load in ~0.7ms against the ~1ms of masking that has
    to happen anyway, and a cache keyed on their file stats had to stat every
    one of them to decide, netting a quarter of a millisecond. Callers mask a
    given body against one `masks()` result (see `masked_hash`), so re-reading
    can't split one body across two mask sets. The returned value doubles as
    the cache key for anything derived from the whole mask set, so a caller
    holding one knows by inequality when its derivation went stale.
    `syspatch.load` calls this at startup so a malformed mask takes the proxy
    down there rather than first surfacing mid-run as an `_uncaught-syspatch`
    incident."""
    return templates.load_templates(MASKS_DIR)


def normalize_body(body: str) -> str:
    """Body with session-volatile regions (cwd, scratchpad path, git status,
    memory paths, cc_version, ...) masked -- stable across sessions that ran
    the same content differently. Which regions, exactly, is `masks.d/`. A
    no-op on text with no such regions, e.g. a traceback."""
    return templates.apply_masks(body, masks())


def digest_of(text: str) -> str:
    """Every store's key, at the width every capture name and incident record
    uses. Deliberately indifferent to whether the text was masked: choosing
    what to pass is the identity/equivalence split, not this function's
    business."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def masked_hash(body: str) -> str:
    """Digest of the body's equivalence class -- the same content sent by two
    sessions that differed only in cwd, git status or scratchpad path hashes
    once. Moves whenever `masks.d/` does, which is why it keys dedup and
    incident records but never a `log/prompt-captures/` filename. A caller that
    also wants the masked text should mask once and hand the result to
    `digest_of`, so one body can't be split across two mask sets."""
    return digest_of(normalize_body(body))


def save_body(body: str, digest: str, capture_dir: Path) -> Path:
    """Store the offending body once at capture_dir/_bodies/{digest}.md, where
    digest is its masked_hash. No-op if already present. The file holds the
    verbatim body (one representative session's environment); the digest keys
    its content, so it is not a checksum of the bytes on disk."""
    bodies_dir = capture_dir / BODIES_DIRNAME
    bodies_dir.mkdir(parents=True, exist_ok=True)
    body_path = bodies_dir / f"{digest}.md"
    if not body_path.exists():
        body_path.write_text(body)
    return body_path


def save_incident(incident: Incident, digest: str, capture_dir: Path) -> Path | None:
    """Write one incident at capture_dir/{rule}/{digest}.json, referencing the
    shared body. Returns the path when freshly written, None when this
    (rule, content) was already recorded — so the caller warns exactly once
    per distinct failure, across restarts."""
    rule_dir = capture_dir / incident.rule
    rule_dir.mkdir(parents=True, exist_ok=True)
    meta_path = rule_dir / f"{digest}.json"
    if meta_path.exists():
        return None
    meta = {
        "at": datetime.now(timezone.utc).isoformat(),
        "rule": incident.rule,
        "kind": incident.kind,
        "body": digest,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return meta_path


def _body_still_live(digest: str, capture_dir: Path) -> bool:
    """True if any non-archived incident, under any rule, still references
    this digest -- a single capture can trip several rules at once
    (e.g. two patches failing to match the same body), so the shared body
    at _bodies/{digest}.md may outlive any one of them being resolved."""
    for rule_dir in capture_dir.iterdir():
        if not rule_dir.is_dir() or rule_dir.name in (BODIES_DIRNAME, ARCHIVE_DIRNAME):
            continue
        if (rule_dir / f"{digest}.json").exists():
            return True
    return False


def archive_incident(rule: str, digest: str, capture_dir: Path) -> None:
    """Move a resolved incident to capture_dir/_archive/{rule}/{digest}.json
    instead of deleting it -- so the data survives long enough to answer
    "what was this" questions, but doesn't accumulate forever (see
    gc_patch_failures.py). The shared body only follows once no other
    live incident still references the digest. Both moved files get their
    mtime reset to now, which is the clock gc reads from -- not the
    incident's original `at` timestamp.
    """
    src = capture_dir / rule / f"{digest}.json"
    if not src.exists():
        return
    dest = capture_dir / ARCHIVE_DIRNAME / rule / f"{digest}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dest)
    dest.touch()

    if not _body_still_live(digest, capture_dir):
        body_src = capture_dir / BODIES_DIRNAME / f"{digest}.md"
        if body_src.exists():
            body_dest = capture_dir / ARCHIVE_DIRNAME / BODIES_DIRNAME / f"{digest}.md"
            body_dest.parent.mkdir(parents=True, exist_ok=True)
            body_src.rename(body_dest)
            body_dest.touch()


def report_issues(body: str, issues: list[Incident], capture_dir: Path | None) -> None:
    """Warn about rules that didn't apply cleanly; when capture_dir is given,
    save the body once (content-addressed) plus one incident record per
    (rule, content) so it can be diagnosed later.

    Capture is idempotent on disk: a body whose content was already recorded
    re-saves nothing and re-warns nothing. The live proxy patches every request,
    so this is what keeps a persistent mismatch from logging endlessly — the
    first request captures and warns, the rest find the record present.
    """
    if capture_dir is None:
        for issue in issues:
            logging.warning("patch %r %s", issue.rule, issue.kind)
        return

    digest = masked_hash(body)
    save_body(body, digest, capture_dir)
    for issue in issues:
        saved = save_incident(issue, digest, capture_dir)
        # logging (not stderr): the console TUI routes records to its event log /
        # status bar; raw stderr corrupts curses. Warn only on a fresh capture.
        if saved is not None:
            logging.warning("patch %r %s -> %s", issue.rule, issue.kind, saved)


def capture_uncaught(rule: str, exc: BaseException, capture_dir: Path | None) -> None:
    """Persist an uncaught exception's traceback the same content-addressed
    way as a patch-application issue, so a bug in an addon hook survives for
    offline triage instead of only flashing through mitmproxy's own log.
    Callers re-raise after this — it captures, it doesn't fail soft."""
    body = "".join(traceback.format_exception(exc))
    if capture_dir is None:
        logging.warning("%s: uncaught %s", rule, type(exc).__name__)
        return
    digest = masked_hash(body)
    save_body(body, digest, capture_dir)
    saved = save_incident(Incident(rule, type(exc).__name__), digest, capture_dir)
    if saved is not None:
        logging.warning("%s: uncaught %s -> %s", rule, type(exc).__name__, saved)
