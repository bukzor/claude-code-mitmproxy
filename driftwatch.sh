#!/bin/bash
# Poll the promotion predicate and print only when its answer changes, so a
# maintenance session can arm it once (Monitor) and be told about upstream
# prompt drift instead of remembering to look for it.
#
# Why polling rather than inotify on log/prompt-captures/: a capture event is a
# superset of a drift event -- most new captures are copies a fixture already
# covers -- and notifying on those spends the attention the signal exists to
# protect. The predicate is the filter, and at a release most days a 60s lag is
# not worth a dependency. Rationale: design/040-design.kb/every-duty-has-an-occasion.md
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SURVEY="${SCRIPT_DIR}/.venv/bin/claude-mitmproxy-survey-captures"
INTERVAL="${DRIFTWATCH_INTERVAL:-60}"

if (( DEBUG > 0 )); then
  set -x
fi

cd "$SCRIPT_DIR"

# Empty, so the first pass always prints: arming the watch reports whatever
# accumulated while no session was open, and an all-clear proves it is live.
previous=''

while true; do
  # The check breaking is itself a signal: a watch that goes quiet when its own
  # predicate crashes is indistinguishable from one reporting no drift. Merging
  # stderr is not enough -- an unexecutable $SURVEY is diagnosed by this shell,
  # outside the substitution, and captures nothing at all -- so the status is
  # read and reported rather than the output being trusted to carry it.
  status=0
  current="$("$SURVEY" --current 2>&1)" || status="$?"
  if (( status != 0 )); then
    current="$(printf 'driftwatch: promotion check exited %s\n%s' "$status" "$current")"
  fi
  if [[ "$current" != "$previous" ]]; then
    printf '%s\n' "$current"
    previous="$current"
  fi
  sleep "$INTERVAL"
done
