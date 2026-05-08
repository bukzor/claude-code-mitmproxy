"""mitmproxy addon: stream requests and responses as separate JSONL lines.

Configured via the `jsonl_path` option (default: /dev/stdout):
    mitmproxy ... -s flow2jsonl.py --set jsonl_path=traffic.jsonl
"""
import base64
import json
from typing import IO, Optional

from mitmproxy import ctx, http


_fp: Optional[IO[str]] = None


def load(loader):
    loader.add_option(
        name="jsonl_path",
        typespec=str,
        default="/dev/stdout",
        help="Path to write request/response JSONL.",
    )


def running():
    global _fp
    _fp = open(ctx.options.jsonl_path, "w", buffering=1)


def done():
    global _fp
    if _fp is not None:
        _fp.close()
        _fp = None


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
    assert _fp is not None
    _fp.write(json.dumps(entry, default=_default) + "\n")


def request(flow: http.HTTPFlow):
    _emit({"phase": "request", "data": flow.request.get_state()})


def response(flow: http.HTTPFlow):
    assert flow.response is not None
    _emit({"phase": "response", "data": flow.response.get_state()})
