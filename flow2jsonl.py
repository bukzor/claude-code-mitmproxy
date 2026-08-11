"""mitmproxy addon: stream requests and responses as separate JSONL lines.

`jsonl_path` (default /dev/stdout) is strftime-formatted and reopened when
the formatted string changes; prefix with "+" for append mode. Mirrors
mitmproxy's own save_stream_file option -- design/040-design.kb/
ease-of-operation.kb/ has the why, including why opening a shard also spawns
compress_traffic.py over the shards already finished.

    mitmproxy ... -s flow2jsonl.py --set jsonl_path=+traffic/%Y-%m-%d.jsonl
"""
import base64
import gzip
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import IO, Optional

from mitmproxy import ctx, http

import incidents

UNCAUGHT_RULE = "_uncaught-flow2jsonl"
COMPRESSOR = Path(__file__).with_name("compress_traffic.py")
COMPRESSOR_LOG = Path(__file__).with_name("log") / "compress_traffic.log"

_fp: Optional[IO[str]] = None
_current_path: Optional[str] = None
_compressed_for: Optional[str] = None
_compressor: Optional[subprocess.Popen] = None


def load(loader):
    loader.add_option(
        name="jsonl_path",
        typespec=str,
        default="/dev/stdout",
        help="Path to write request/response JSONL. strftime-formatted; "
        "prefix with + to append instead of overwrite.",
    )


def _rotate_if_needed():
    """Reopen the output file when today's formatted jsonl_path differs from
    the currently open one."""
    global _fp, _current_path
    spec = ctx.options.jsonl_path
    append = spec.startswith("+")
    path = datetime.today().strftime(spec[1:] if append else spec)
    if path == _current_path and _fp is not None:
        return
    if _fp is not None:
        _fp.close()
        _fp = None
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    _fp = open(path, "a" if append else "w", buffering=1)
    _current_path = path


def done():
    global _fp, _current_path
    if _fp is not None:
        _fp.close()
        _fp = None
    _current_path = None


def _compress_finished_shards():
    """Spawn compress_traffic.py over every shard that is no longer today's.

    Called once per shard this process opens -- including the first one, at
    startup -- and from the end of the response hook rather than from the
    open itself. Both choices are load-bearing; see
    design/040-design.kb/ease-of-operation.kb/compression-at-shard-open.md.
    """
    global _compressor
    if _compressor is not None and _compressor.poll() is None:
        return  # yesterday's run is still going; don't stack them
    COMPRESSOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with COMPRESSOR_LOG.open("a") as log:
        log.write(f"--- {datetime.today():%Y-%m-%d %H:%M:%S}\n")
        log.flush()
        _compressor = subprocess.Popen(
            [sys.executable, str(COMPRESSOR)],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # outlives a Ctrl-C on the proxy
        )


def _default(obj):
    """json.dumps default handler for bytes."""
    if not isinstance(obj, bytes):
        raise TypeError(type(obj))
    try:
        obj = gzip.decompress(obj)
    except gzip.BadGzipFile:
        pass
    try:
        return json.loads(obj)
    except json.JSONDecodeError:
        return obj.decode("utf-8")
    except UnicodeDecodeError:
        return base64.b64encode(obj).decode("ascii")


def _emit(entry: dict):
    _rotate_if_needed()
    assert _fp is not None
    _fp.write(json.dumps(entry, default=_default) + "\n")


def request(flow: http.HTTPFlow):
    try:
        _emit({"phase": "request", "data": flow.request.get_state()})
    except Exception as exc:
        incidents.capture_uncaught(UNCAUGHT_RULE, exc, incidents.CAPTURE_DIR)
        raise


def response(flow: http.HTTPFlow):
    global _compressed_for
    try:
        assert flow.response is not None
        _emit({"phase": "response", "data": flow.response.get_state()})
        if _compressed_for != _current_path:
            # Once per shard opened, so a reopen that self-heals a lost handle
            # doesn't re-spawn against the same one.
            _compressed_for = _current_path
            _compress_finished_shards()
    except Exception as exc:
        incidents.capture_uncaught(UNCAUGHT_RULE, exc, incidents.CAPTURE_DIR)
        raise
