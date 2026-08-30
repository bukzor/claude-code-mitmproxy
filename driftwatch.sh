#!/bin/bash
# Re-evaluate the promotion predicate whenever its inputs change, and print only
# when its answer changes, so a maintenance session can arm it once (Monitor)
# and be told about upstream prompt drift instead of remembering to look.
#
# inotify only decides *when to look*; the predicate still decides what is worth
# saying. That split is the whole design -- a capture event is a superset of a
# drift event, so waking on one is right and notifying on one would not be.
# Rationale: design/040-design.kb/every-duty-has-an-occasion.md
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

# Everything the predicate reads. system-prompts.kb/ and blocks.d/ are not
# optional: promoting a fixture is what clears a standing report, and watching
# only the captures would leave it red until the next unrelated capture.
WATCHED=(log/prompt-captures system-prompts.kb blocks.d)

# Write-side events only. `access`/`open` would be woken by the predicate's own
# reads of these very files, which is a spin, not a watch.
EVENTS=close_write,create,delete,moved_to,moved_from

# A re-check ceiling, not a poll interval: it covers a change landing in the
# window between a check and the next wait, and keeps a watch that quietly
# stopped working from being indistinguishable from no drift.
FLOOR="${DRIFTWATCH_FLOOR:-300}"

if (( DEBUG > 0 )); then
  set -x
fi

cd "$SCRIPT_DIR"

wait_for_change() {
  # Blocks until an input changes or the ceiling expires. inotifywait exits 2
  # on that timeout, which is normal; any other failure means the watcher
  # itself is unusable, so fall back to sleeping and let the loop degrade to
  # polling at the ceiling rate rather than spinning or dying.
  local status=0
  inotifywait -qq -t "$FLOOR" -e "$EVENTS" "${WATCHED[@]}" || status="$?"
  if (( status != 0 && status != 2 )); then
    sleep "$FLOOR"
  fi
}

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
  wait_for_change
done
