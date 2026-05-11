#!/bin/bash
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

if (( DEBUG > 0 )); then
  set -x
fi

# Extract the agent system-prompt body from a traffic.jsonl capture.
# Bodies are identical across requests in a session, so we print the first.
JSONL_FILE="${1:?usage: jsonl2sysprompt.sh <traffic.jsonl>}"

jq -rn '
  first(
    inputs
    | select(.phase == "request")
    | .data.content.system[]?
    | select(.type == "text" and (.text | startswith("\nYou are an interactive agent")))
    | .text
  ) // error("no system-prompt body found")
' "$JSONL_FILE"
