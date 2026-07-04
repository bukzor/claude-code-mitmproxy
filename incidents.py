"""Content-addressed capture for addon incidents: shared by syspatch.py's
patch-application issues and any addon hook's uncaught exceptions. Capture is
idempotent on disk, keyed by content_hash, so a live proxy re-hitting the same
failure on every request logs and writes exactly once."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

# Gitignored; callers pass capture_dir=None to disable capture entirely
# (offline callers like check_patches only want an in-process warning).
CAPTURE_DIR = Path(__file__).parent / "patch-failures"
BODIES_DIRNAME = "_bodies"

# Per-session-volatile regions that differ between otherwise-identical bodies
# (cwd, scratchpad path, git status + recent commits). Neutralized only for
# the dedup hash; the stored body keeps them verbatim for diagnosis. A no-op
# on text with no such lines, e.g. a traceback.
_VOLATILE_SUBS = (
    (re.compile(r"\ngitStatus:.*", re.DOTALL), "\n"),
    (re.compile(r"(?m)^( - Primary working directory:).*"), r"\1"),
    (re.compile(r"(?m)^`/tmp/.*scratchpad`$"), "`scratchpad`"),
)


class Incident(NamedTuple):
    rule: str
    kind: str


def content_hash(body: str) -> str:
    """Hash identifying the captured text, stable across sessions: the
    per-session environment tail (cwd, scratchpad path, git status) is
    neutralized first, so the same content dedups to a single incident
    instead of one per session that happened to run it differently."""
    normalized = body
    for pattern, repl in _VOLATILE_SUBS:
        normalized = pattern.sub(repl, normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def save_body(body: str, digest: str, capture_dir: Path) -> Path:
    """Store the offending body once at capture_dir/_bodies/{digest}.md, where
    digest is its content_hash. No-op if already present. The file holds the
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


def capture_uncaught(rule: str, exc: BaseException, capture_dir: Path | None) -> None:
    """Persist an uncaught exception's traceback the same content-addressed
    way as a patch-application issue, so a bug in an addon hook survives for
    offline triage instead of only flashing through mitmproxy's own log.
    Callers re-raise after this — it captures, it doesn't fail soft."""
    body = "".join(traceback.format_exception(exc))
    if capture_dir is None:
        logging.warning("%s: uncaught %s", rule, type(exc).__name__)
        return
    digest = content_hash(body)
    save_body(body, digest, capture_dir)
    saved = save_incident(Incident(rule, type(exc).__name__), digest, capture_dir)
    if saved is not None:
        logging.warning("%s: uncaught %s -> %s", rule, type(exc).__name__, saved)
