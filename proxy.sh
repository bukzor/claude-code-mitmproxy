#!/bin/bash
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Every file in ADDON_DIR appears below and vice versa; see its __init__.py.
ADDON_DIR="${SCRIPT_DIR}/lib/claude_mitmproxy/addons"
# The addons import the library beside them by package name. mitmproxy
# path-loads each one as `__mitmproxy_script__.<stem>` and puts only that
# file's own directory on sys.path, so the package has to be findable
# independently -- and by the same name in the compressor subprocess
# flow2jsonl spawns, which inherits this env.
export PYTHONPATH="${SCRIPT_DIR}/lib${PYTHONPATH:+:${PYTHONPATH}}"
PORT="${1:-8080}"
# strftime path, append mode: shards by day, survives restarts -- see
# design/040-design.kb/ease-of-operation.kb/.
FLOW_FILE="+${SCRIPT_DIR}/log/traffic/%Y-%m-%d.flow"
JSONL_FILE="+${SCRIPT_DIR}/log/traffic/%Y-%m-%d.jsonl"

if (( DEBUG > 0 )); then
  set -x
fi

mitmproxy \
  --mode "reverse:https://api.anthropic.com" \
  --listen-port "$PORT" \
  -w "$FLOW_FILE" \
  -s "${ADDON_DIR}/reload.py" \
  -s "${ADDON_DIR}/syscapture.py" \
  -s "${ADDON_DIR}/syspatch.py" \
  -s "${ADDON_DIR}/toolpatch.py" \
  -s "${ADDON_DIR}/thinkpatch.py" \
  -s "${ADDON_DIR}/flow2jsonl.py" \
  --set "jsonl_path=${JSONL_FILE}"
