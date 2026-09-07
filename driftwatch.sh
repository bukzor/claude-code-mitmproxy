#!/bin/bash
# Run the promotion pass whenever its inputs change, and print only when its
# report changes, so a maintenance session can arm it once (Monitor) and be
# handed what the pass did -- each fixture it filed with a glance at its diff
# from the nearest sibling -- instead of remembering to look. The incident
# queue rides along the same way. Every line that asks something of the reader
# starts with its event type, which is the key into playbook.kb/.
#
# inotify only decides *when to look*; the pass still decides what is worth
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
GC="${SCRIPT_DIR}/.venv/bin/claude-mitmproxy-gc-patch-failures"

# What the pass reads, one signal per input. system-prompts.kb/ and blocks.d/
# are not optional: a committed fixture is what clears a standing report, and
# watching only the captures would leave it red until the next unrelated
# capture. The pass's own commit lands there too, and the wake it causes is
# the pass confirming its all-clear. log/events/incident is the queue's
# signal: a fresh incident record is announced there, so the queue line moves
# exactly when the queue does.
#
# log/events/capture rather than log/prompt-captures, which is the same news
# through a noisier door: a masks.d/ edit makes the next request rewrite every
# stale masked sibling, up to ~150 close_writes in a burst, each costing a
# re-derivation of a predicate that does not read them.
WATCHED=(log/events/capture log/events/incident system-prompts.kb blocks.d)

# The events file is appended through an fd the proxy holds open for its
# lifetime, so a capture event arrives as `modify` and its `close_write` comes
# only when the proxy exits -- watching for the close alone is a watch that
# never fires. Still write-side only: `access`/`open` would be woken by the
# pass's own reads of these very files, which is a spin, not a watch.
EVENTS=modify,close_write,create,delete,moved_to,moved_from

# A re-check ceiling, not a poll interval: it covers a change landing in the
# window between a check and the next wait, and keeps a watch that quietly
# stopped working from being indistinguishable from no drift. An hour because
# the ceiling, not the wakes, is what this costs: at 300s it accounted for 288
# of ~290 daily wakes against ~4 real capture events, so it -- not which
# directory is watched -- is the whole bill.
FLOOR="${DRIFTWATCH_FLOOR:-3600}"

if (( DEBUG > 0 )); then
  set -x
fi

cd "$SCRIPT_DIR"

# An events directory is created by the first event of its kind, which may be
# days out; inotifywait on a missing path fails, and this loop answers a failed
# watch by degrading to polling at the ceiling. Make the precondition true
# instead of discovering it as an hourly poll.
mkdir -p log/events/capture log/events/incident

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

report() {
  # Run one tool and print what it said, its failure reported ahead of that:
  # a watch that goes quiet when its own tool crashes is indistinguishable
  # from one reporting nothing. Merging stderr is not enough -- an
  # unexecutable tool is diagnosed by this shell, outside the substitution,
  # and captures nothing at all -- so the status is read and reported rather
  # than the output being trusted to carry it.
  local status=0 output
  output="$("$@" 2>&1)" || status="$?"
  if (( status != 0 )); then
    printf 'driftwatch: %s exited %s\n' "${1##*/}" "$status"
  fi
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output"
  fi
}

# Empty, so the first pass always prints: arming the watch reports whatever
# accumulated while no session was open, and an all-clear proves it is live.
previous=''

while true; do
  current="$(report "$SURVEY" --promote; report "$GC" --queue)"
  if [[ "$current" != "$previous" ]]; then
    printf '%s\n' "$current"
    previous="$current"
  fi
  wait_for_change
done
