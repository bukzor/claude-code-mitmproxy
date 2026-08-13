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
ADDON="${SCRIPT_DIR}/lib/claude_mitmproxy/addons/flow2jsonl.py"
# The addon imports the package; mitmproxy only puts the addon's own directory
# on sys.path (see proxy.sh).
export PYTHONPATH="${SCRIPT_DIR}/lib${PYTHONPATH:+:${PYTHONPATH}}"

if (( DEBUG > 0 )); then
  set -x
fi

# Replay a .flow file through the addon, stream JSONL to stdout.
FLOW_FILE="${1:?usage: flow2jsonl.sh <traffic.flow>}"

mitmdump -n -r "$FLOW_FILE" -s "$ADDON" -q
