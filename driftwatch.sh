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

# What the predicate reads, one signal per input. system-prompts.kb/ and
# blocks.d/ are not optional: promoting a fixture is what clears a standing
# report, and watching only the captures would leave it red until the next
# unrelated capture. Neither is a proxy event -- a fixture is promoted by hand
# -- so only the capture side can be an events file.
#
# log/events/capture rather than log/prompt-captures, which is the same news
# through a noisier door: a masks.d/ edit makes the next request rewrite every
# stale masked sibling, up to ~150 close_writes in a burst, each costing a
# re-derivation of a predicate that does not read them.
WATCHED=(log/events/capture system-prompts.kb blocks.d)

# The events file is appended through an fd the proxy holds open for its
# lifetime, so a capture event arrives as `modify` and its `close_write` comes
# only when the proxy exits -- watching for the close alone is a watch that
# never fires. Still write-side only: `access`/`open` would be woken by the
# predicate's own reads of these very files, which is a spin, not a watch.
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

# The events directory is created by the first event of its kind, which may be
# days out; inotifywait on a missing path fails, and this loop answers a failed
# watch by degrading to polling at the ceiling. Make the precondition true
# instead of discovering it as an hourly poll.
mkdir -p log/events/capture

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
