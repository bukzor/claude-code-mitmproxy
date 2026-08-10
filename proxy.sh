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
  -s "${SCRIPT_DIR}/reload.py" \
  -s "${SCRIPT_DIR}/syscapture.py" \
  -s "${SCRIPT_DIR}/syspatch.py" \
  -s "${SCRIPT_DIR}/toolpatch.py" \
  -s "${SCRIPT_DIR}/thinkpatch.py" \
  -s "${SCRIPT_DIR}/flow2jsonl.py" \
  --set "jsonl_path=${JSONL_FILE}"
