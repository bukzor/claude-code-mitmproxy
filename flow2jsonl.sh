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
ADDON="${SCRIPT_DIR}/flow2jsonl.py"

if (( DEBUG > 0 )); then
  set -x
fi

# Read .flow file(s) from args, replay through addon, stream JSONL to stdout
FLOW_FILE="${1:?usage: flow2jsonl.sh <traffic.flow>}"

tail -f -c +0 "$FLOW_FILE" |
  mitmdump -n -r - -s "$ADDON" -q
