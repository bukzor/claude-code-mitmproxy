"""mitmproxy addon: stream requests and responses as separate JSONL lines.

`jsonl_path` (default /dev/stdout) is strftime-formatted and reopened when
the formatted string changes; prefix with "+" for append mode. Mirrors
mitmproxy's own save_stream_file option -- design/040-design.kb/
ease-of-operation.kb/ has the why.

    mitmproxy ... -s flow2jsonl.py --set jsonl_path=+traffic/%Y-%m-%d.jsonl
"""
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import IO, Optional

from mitmproxy import ctx, http

from incidents import CAPTURE_DIR, capture_uncaught

UNCAUGHT_RULE = "_uncaught-flow2jsonl"

_fp: Optional[IO[str]] = None
_current_path: Optional[str] = None


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


def _default(obj):
    """json.dumps default handler for bytes."""
    if not isinstance(obj, bytes):
        raise TypeError(type(obj))
    try:
        import gzip
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
        capture_uncaught(UNCAUGHT_RULE, exc, CAPTURE_DIR)
        raise


def response(flow: http.HTTPFlow):
    try:
        assert flow.response is not None
        _emit({"phase": "response", "data": flow.response.get_state()})
    except Exception as exc:
        capture_uncaught(UNCAUGHT_RULE, exc, CAPTURE_DIR)
        raise
