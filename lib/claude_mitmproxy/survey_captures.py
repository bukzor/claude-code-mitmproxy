#!/usr/bin/env python3
"""Inventory of captured system-prompt bodies: one row per raw capture in
log/prompt-captures/, classified by prompt shape, with the session-optional
blocks it carries and whether its exact body is already promoted into
system-prompts.kb/. The plain table is the way to read what is on disk; the
flags answer what is missing from it.

`--drift` answers that directly instead of leaving it to the eye: one row per
prompt copy (shape + core digest) that no fixture covers, newest first, naming
the raw to promote. At ~100 captures the table is not the way to spot what is
missing.

`--current` narrows that to the copies carried at the newest release -- the
predicate that earns an interruption. Everything it drops is backlog, which is
why the full drift table is the wrong thing to wire a signal to.

`--promote` answers it instead of printing it: every current row copied into
`system-prompts.kb/` under a name derived from the capture, glanced at, and
committed. Nothing is chosen, so nothing is left for a reader to decide -- see
`promote` for why what remained of this duty was toil, and `promotion_pass` for
what is still worth a look and how `driftwatch.sh` hands it over.

Usage: survey_captures.py [--drift] [--current] [--promote] [SUBSTRING ...]
Rows are filtered to filenames containing any SUBSTRING (e.g. "2.1.221").
"""
from __future__ import annotations

import difflib
import itertools
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

from claude_mitmproxy import incidents
from claude_mitmproxy import logging_handlers
from claude_mitmproxy import prompt_shape
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates

CAPTURES_DIR = Path("log/prompt-captures")
KB_DIR = Path("system-prompts.kb")


class Capture(NamedTuple):
    version: str  # cc_version incl. build tag, e.g. "2.1.221.b87"
    model: str
    raw: str  # digest of the body as sent -- the capture's identity and name
    path: Path

    @property
    def release(self) -> tuple[int, ...]:
        """The numeric version, build tag dropped.

        Build tags are hashes, so ordering two of them is noise -- only the
        release orders. Keeping them apart is what lets `current_drift` ask
        whether upstream is serving a copy now instead of whether its capture
        happened to carry the highest-sorting tag."""
        release, _, _ = self.version.rpartition(".")
        return tuple(int(part) for part in release.split("."))

    @property
    def sort_key(self) -> tuple:
        _, _, build = self.version.rpartition(".")
        return self.release + (build, self.model)


def parse_name(path: Path) -> Capture:
    stem = path.name.removesuffix(".raw.md")
    version, model, raw = stem.rsplit("_", 2)
    assert version.startswith("v"), path
    return Capture(version.removeprefix("v"), model, raw, path)


def core_of(text: str, blocks: tuple[rule_templates.Template, ...]) -> tuple[str, str]:
    """The capture's (core digest, session-optional blocks it carries).

    The core digest is what's left once every block this session happened to
    switch on is deleted: two captures share it exactly when they carry the
    same prompt copy, whatever their sessions differed on. Blocks are stripped
    from the masked body, so a block template can be written against the
    tokens masks leave behind instead of the volatile text they replaced."""
    stripped, present = rule_templates.strip_blocks(incidents.normalize_body(text), blocks)
    return incidents.digest_of(stripped), ",".join(present)


def promoted_as(text: str, kb_texts: dict[str, str]) -> str:
    return next((name for name, kb in kb_texts.items() if kb == text), "")


class Surveyed(NamedTuple):
    """One capture, with everything the two views derive from it."""

    capture: Capture
    text: str
    core: str
    blocks: str
    shape: str
    promoted: str


class Drift(NamedTuple):
    """One prompt copy no fixture covers, and the raw that would cover it."""

    shape: str
    core: str
    span: str
    size: int
    candidate: Capture
    newest: Capture  # latest capture of this copy -- what dates it


def survey(
    captures: list[Capture], kb_texts: dict[str, str], blocks: tuple[rule_templates.Template, ...]
) -> list[Surveyed]:
    rows = []
    for capture in sorted(captures, key=lambda c: c.sort_key):
        text = capture.path.read_text()
        core, present = core_of(text, blocks)
        rows.append(
            Surveyed(
                capture,
                text,
                core,
                present,
                prompt_shape.shape_of(text),
                promoted_as(text, kb_texts),
            )
        )
    return rows


def promoted_cores(
    kb_texts: dict[str, str], blocks: tuple[rule_templates.Template, ...]
) -> set[tuple[str, str]]:
    """The (shape, core) pairs the fixtures already cover.

    Taken from the fixtures themselves rather than from whichever captures
    happen to equal one: a fixture outlives the capture it was promoted from,
    and reading it off the captures would call its copy uncovered once the
    capture is gone."""
    return {
        (prompt_shape.shape_of(text), core_of(text, blocks)[0])
        for text in kb_texts.values()
    }


def drifted(rows: list[Surveyed], covered: set[tuple[str, str]]) -> list[Drift]:
    """Uncovered prompt copies, newest first within each shape.

    Grouped by (shape, core) because the promotion decision is per copy, not
    per capture: a hundred captures of one copy need one fixture. Old
    uncovered copies stay listed -- they are the context that says whether the
    newest one is a fresh rewrite or the latest of a drifting series -- but
    they sort below it, since only the newest is a duty."""
    groups: dict[tuple[str, str], list[Surveyed]] = {}
    for row in rows:
        key = (row.shape, row.core)
        if key not in covered:
            groups.setdefault(key, []).append(row)

    dated = []
    for (shape, core), members in groups.items():
        by_age = sorted(members, key=lambda r: r.capture.sort_key)
        fullest = max(members, key=lambda r: len(r.text))
        oldest, newest = by_age[0].capture, by_age[-1].capture
        dated.append((
            newest.sort_key,
            Drift(
                shape=shape,
                core=core,
                span=(
                    oldest.version
                    if oldest.version == newest.version
                    else f"{oldest.version}..{newest.version}"
                ),
                size=len(fullest.text),
                candidate=fullest.capture,
                newest=newest,
            ),
        ))

    # Two passes, leaning on a stable sort: recency descending first, then
    # shape ascending, which preserves it within each shape. One pass can't
    # do it -- sort_key mixes ints and strings, so it has no negation.
    dated.sort(key=lambda pair: pair[0], reverse=True)
    dated.sort(key=lambda pair: pair[1].shape)
    return [drift for _, drift in dated]


def current_drift(drifts: list[Drift], captures: list[Capture]) -> list[Drift]:
    """The uncovered copies upstream is serving now -- the ones that earn an
    interruption (`design/040-design.kb/every-duty-has-an-occasion.md`).

    The rest of the drift table is backlog: real, but no evidence anything
    moved, and a signal that fires on it is red forever. Newest release across
    every shape rather than per shape, since a shape absent from newer releases
    is one upstream stopped serving."""
    assert captures, "no captures to date: 'nothing uncovered' would be vacuous"
    newest = max(capture.release for capture in captures)
    return [drift for drift in drifts if drift.newest.release == newest]


def fixture_name(drift: Drift) -> str:
    """What a copy is promoted *as* -- derived, never chosen.

    Release, shape and raw digest are all readable off the capture, so two
    promoters agree and neither has to know which copy arrived first. The raw
    digest rather than the core: core digests move whenever `blocks.d/`
    changes, and a name a rule edit can invalidate is what
    `design/040-design.kb/content-addressed-capture.md` forbids.
    """
    release = ".".join(str(part) for part in drift.candidate.release)
    suffix = prompt_shape.FIXTURE_SUFFIX[drift.shape]
    return f"v{release}{suffix}-{drift.candidate.raw[:8]}.md"


class Filed(NamedTuple):
    """One fixture the pass filed -- or found already filed by an earlier pass
    whose commit was refused, and is taking up again."""

    fixture: Path
    drift: Drift
    fresh: bool


def promote(drifts: list[Drift], kb_dir: Path) -> tuple[list[Filed], list[str]]:
    """Copy each uncovered copy's raw body into the fixture collection.

    Nothing here decides anything, which is the point. Since "promote every
    one of them" there is no winner to pick, and with `check_patches` reading
    every fixture at the newest release there is no privileged name to award
    either -- so what was left of this duty was a human performing a `cp` that
    a function can derive. A duty with no decision in it is toil, and
    `design/040-design.kb/every-duty-has-an-occasion.md` says to bind that to
    its occasion rather than report it. The occasion is the commit that
    follows: touching `system-prompts.kb/` runs the whole offline suite.

    A shape this repo has no marker for is the exception, and it stays a
    human's: it has no derivable name, and a body carrying no known marker is
    the one drift worth reading rather than filing.

    A target already on disk with this very body is what a refused commit
    leaves behind (`commit_promotions`), and is taken up again rather than
    refused: the collection is what is committed (`committed_fixtures`), so
    the copy still reads as uncovered until the commit stands. The same name
    over a different body is a bug in the naming, and stops here.
    """
    written, skipped = [], []
    for drift in drifts:
        if drift.shape not in prompt_shape.FIXTURE_SUFFIX:
            skipped.append(f"unknown shape {drift.shape}, read it yourself: {drift.candidate.path}")
            continue
        target = kb_dir / fixture_name(drift)
        body = drift.candidate.path.read_text()
        if target.exists():
            assert target.read_text() == body, (target, "already on disk with a different body")
            written.append(Filed(target, drift, fresh=False))
        else:
            target.write_text(body)
            written.append(Filed(target, drift, fresh=True))
    return written, skipped


def commit_message(promoted: list[Filed]) -> str:
    """What the promoting commit says, which is what it did and nothing else.

    Derived like the names are: a message claiming why upstream changed would
    be a guess, and the diff already carries the bodies."""
    releases = sorted({filed.fixture.stem.split("-")[0] for filed in promoted})
    lines = [
        f"Promote {len(promoted)} prompt {'copy' if len(promoted) == 1 else 'copies'}"
        f" at {', '.join(releases)}",
        "",
        "Filed by `survey-captures --promote`. Every name derives from its",
        "capture -- release, shape, raw digest -- so nothing here was chosen.",
        "",
    ]
    lines += [f"  {filed.fixture.name} <- {filed.drift.candidate.path.name}" for filed in promoted]
    return "\n".join(lines) + "\n"


class CommitResult(NamedTuple):
    returncode: int
    output: str  # stdout then stderr: the hook's verdict, when there is one


def commit_promotions(promoted: list[Filed]) -> CommitResult:
    """Commit what was just written, letting the hook decide whether it stands.

    Promotion *can* go wrong, in one way worth naming: an unruled
    session-optional block makes two captures of one copy read as two copies,
    and the fixture then carries that block inside its core, inflating the
    `_strip-rate` floor `strip_floors` derives from it until ordinary traffic
    trips it. Committing is not what risks that -- writing the file is -- and
    committing is what *catches* it, because a commit touching
    `system-prompts.kb/` runs the whole offline suite, `check_strip_floors`
    included (`.pre-commit-config.yaml`).

    So a red hook is the occasion this duty always wanted: the files stay in
    the working tree, uncommitted and named, the next pass takes them up again
    (`promote`), and a human looks exactly when something is wrong instead of
    every time. Never pushes -- publishing stays an act someone performs.
    """
    paths = [str(filed.fixture) for filed in promoted]
    done = subprocess.run(
        ["git", "commit-files", *paths, "--", "-m", commit_message(promoted)],
        capture_output=True,
        text=True,
    )
    return CommitResult(done.returncode, done.stdout + done.stderr)


# Past this many changed lines the diff is summarised rather than printed. The
# glance is for a *small* diff -- flawed deduplication shows as a fixture a few
# lines from a sibling -- and a large one says "genuinely new" by its size
# alone, at a cost in lines the Monitor channel would stop the watch for.
GLANCE_LINES = 120

# The nearest-sibling search is quadratic in the collection and cheap at its
# size; this is the tripwire for the size nobody has seen yet
# (`design/040-design.kb/loudness-policy.md`). Overrunning it is reported and
# never acted on: the report is the moment to build an index, not a reason
# for the pass to skip its glance.
DIFF_BUDGET_SECONDS = 30.0


class Nearest(NamedTuple):
    """The fixture a body most resembles, and what finding it cost."""

    stem: str  # the body's own fixture name, sans suffix
    name: str  # the nearest sibling's
    distance: int
    diff: str
    compared: int
    seconds: float


def distance(a: str, b: str) -> int:
    """Lines that differ between two bodies: each line removed or added counts
    one, so a one-line rewrite is 2 and an appended line is 1."""
    diff = difflib.unified_diff(a.splitlines(), b.splitlines(), n=0, lineterm="")
    # Two file headers first; after them, with no context lines, everything
    # that is not a hunk header is a change.
    return sum(1 for line in itertools.islice(diff, 2, None) if not line.startswith("@@"))


def nearest_fixture(stem: str, text: str, others: dict[str, str]) -> Nearest:
    """The sibling with the smallest diff, found by diffing against every one.

    Nearest means smallest diff and nothing cleverer (ruled 2026-09-01: "What
    *I* would mean is the fixture with the smallest diff"): an index would
    guess at which siblings are worth comparing, and a mis-split copy is
    exactly the one the guess would miss."""
    assert others, (stem, "nothing to compare against")
    started = time.monotonic()
    distances = {name: distance(other, text) for name, other in others.items()}
    seconds = time.monotonic() - started
    name = min(distances, key=distances.__getitem__)
    diff = "\n".join(
        difflib.unified_diff(
            others[name].splitlines(), text.splitlines(), fromfile=name, tofile=stem, n=1, lineterm=""
        )
    )
    return Nearest(stem, name, distances[name], diff, len(others), seconds)


def glance(nearest: Nearest, kb_dir: Path) -> str:
    """What a reader is shown of a promotion: the diff when it is small enough
    to read in the channel, else where to run it."""
    if nearest.distance <= GLANCE_LINES:
        return nearest.diff + "\n"
    return (
        f"diff of {nearest.distance} lines not shown:"
        f" diff {kb_dir / nearest.name}.md {kb_dir / nearest.stem}.md\n"
    )


def read_fixtures(kb_dir: Path) -> dict[str, str]:
    """Every fixture on disk, by stem -- the pool a glance searches."""
    return {p.stem: p.read_text() for p in sorted(kb_dir.glob("*.md")) if p.name != "CLAUDE.md"}


def committed_fixtures(kb_dir: Path) -> dict[str, str]:
    """The fixtures at HEAD, by stem -- what coverage is read from.

    The collection is what is committed. A fixture a refused commit left on
    disk covers nothing yet: read as coverage, its copy stops drifting, the
    pass stops taking it up, and the refusal is never seen again. HEAD's tree
    rather than the index, which a refused commit may have left staged."""
    listed = subprocess.run(
        ["git", "-C", str(kb_dir), "ls-tree", "-z", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    names = [name for name in listed.split("\0") if name.endswith(".md") and name != "CLAUDE.md"]
    return {Path(name).stem: (kb_dir / name).read_text() for name in sorted(names)}


def all_clear(current: bool) -> str:
    """No count in it: a count changes when a covered capture arrives, and a
    watch that prints on change would announce nothing as if it were
    something."""
    return "no uncovered prompt copies" + (" at the newest release" if current else "")


def without_durations(hook_output: str) -> str:
    """pytest's ` in 2.31s` stripped. A refused promotion is taken up again on
    every pass, and its output has to read the same each time, or the watch,
    which prints on change, would announce one refusal at every wake."""
    return re.sub(r" in \d+\.\d+s\b", "", hook_output)


def say(event: logging.Logger, level: int, message: str, *args: object) -> str:
    """Record the event and return its line for the reader, keyed by the type.

    One spelling for both: the key is what the reader looks up in
    `playbook.kb/`, and the record is what a later reader greps."""
    event.log(level, message, *args)
    return f"{logging_handlers.event_key(event)} {message % args}\n"


def promotion_pass(drifts: list[Drift], kb_dir: Path) -> str:
    """File, glance, commit, and say what happened.

    Every line that asks something of a reader starts with its event type;
    `committed N` asks nothing and carries none. The lines read the same from
    one pass to the next while nothing changes, because the watch prints on
    change: so the glance carries the deterministic figures only, and the
    search's timing goes to the event record -- written once per fixture,
    where a fixture taken up again re-prints its glance every pass.
    """
    promotion = logging_handlers.events.promotion
    written, skipped = promote(drifts, kb_dir)
    out = [say(promotion.declined, logging.WARNING, "%s", reason) for reason in skipped]

    fixtures = read_fixtures(kb_dir)
    compared, seconds = 0, 0.0
    for filed in written:
        stem = filed.fixture.stem
        others = {name: body for name, body in fixtures.items() if name != stem}
        nearest = nearest_fixture(stem, fixtures[stem], others)
        compared += nearest.compared
        seconds += nearest.seconds
        line = (
            f"{filed.fixture.name} <- {filed.drift.candidate.path.name}"
            f" nearest={nearest.name} distance={nearest.distance}"
        )
        if filed.fresh:
            promotion.filed.info("%s compared=%d seconds=%.2f", line, nearest.compared, nearest.seconds)
        out.append(f"{logging_handlers.event_key(promotion.filed)} {line}\n")
        out.append(glance(nearest, kb_dir))
    if seconds > DIFF_BUDGET_SECONDS:
        out.append(
            say(
                promotion.over_budget,
                logging.WARNING,
                "compared=%d seconds=%.0f budget=%.0f",
                compared,
                seconds,
                DIFF_BUDGET_SECONDS,
            )
        )

    if written:
        done = commit_promotions(written)
        if done.returncode == 0:
            out.append(f"committed {len(written)} fixture{'' if len(written) == 1 else 's'}\n")
        else:
            names = ", ".join(filed.fixture.name for filed in written)
            out.append(say(promotion.refused, logging.WARNING, "exit %d: %s", done.returncode, names))
            out.append(without_durations(done.output).strip() + "\n")
    return "".join(out)


def inventory_table(rows: list[Surveyed]) -> list[tuple[str, ...]]:
    header = ("version", "model", "raw", "core", "bytes", "shape", "promoted", "blocks")
    return [header] + [
        (
            row.capture.version,
            row.capture.model.removeprefix("claude-"),
            row.capture.raw,
            row.core,
            str(len(row.text)),
            row.shape,
            row.promoted,
            row.blocks,
        )
        for row in rows
    ]


def drift_table(drifts: list[Drift]) -> list[tuple[str, ...]]:
    header = ("shape", "core", "versions", "bytes", "promote")
    return [header] + [
        (
            drift.shape,
            drift.core,
            drift.span,
            str(drift.size),
            str(drift.candidate.path),
        )
        for drift in drifts
    ]


def trailer(count: int, current: bool) -> str:
    """What the reader should do with the table above."""
    if current:
        return (
            f"{count} uncovered at the newest release: upstream is serving prompt"
            " text no fixture covers, so every patch verified against a fixture is"
            " unverified against what ships. `--promote` files every row and"
            " names it; copies of one shape coexist while upstream reworks it,"
            " and covering all of them is what makes this quiet."
        )
    else:
        return (
            f"{count} uncovered copies."
            " Only the newest release is a duty (`--current`); the rest is backlog,"
            " left uncovered because promotion tracks what upstream serves now."
        )


def render(rows: list[tuple[str, ...]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "".join(
        "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() + "\n"
        for row in rows
    )


class Args(NamedTuple):
    drift: bool
    current: bool
    promote: bool
    filters: list[str]


FLAGS = ("--drift", "--current", "--promote")


def parse_argv(argv: list[str]) -> Args:
    """The flags, plus name substrings to narrow the captures.

    An unrecognized flag is refused rather than taken as a filter. `--data-only`
    is the one that provokes it -- a real convention, but of the `check_*`
    commands, and this is a tool with no verdict to suppress -- and as a filter
    it matched no capture and reported "no uncovered prompt copies": a
    confident, wrong, and entirely silent answer to the one
    question this tool exists to ask."""
    filters = [arg for arg in argv if arg not in FLAGS]
    unknown = [arg for arg in filters if arg.startswith("-")]
    assert not unknown, (unknown, "unknown flag; other arguments are name substrings")
    promote = "--promote" in argv
    current = "--current" in argv or promote
    return Args("--drift" in argv or current, current, promote, filters)


def main() -> None:
    args = parse_argv(sys.argv[1:])
    if args.promote:
        # An offline emitter: its events go only into the domain no proxy
        # process writes (`events.promotion`), which is what keeps one writer
        # per shard. Root gets a null handler so logging's last-resort handler
        # does not print each warning a second time on stderr -- the pass's
        # own report already carries every one of them.
        logging.getLogger().addHandler(logging.NullHandler())
        logging_handlers.reinstall_log_handlers()
    raws = sorted(CAPTURES_DIR.glob("*.raw.md"))
    assert raws, CAPTURES_DIR
    captures = [
        parse_name(path)
        for path in raws
        if not args.filters or any(f in path.name for f in args.filters)
    ]
    assert captures, (args.filters, "matched no capture; every answer below would be vacuous")
    kb_texts = committed_fixtures(KB_DIR)

    blocks = rule_templates.load_templates(prompt_patches.BLOCKS_DIR)
    rows = survey(captures, kb_texts, blocks)

    if args.drift:
        drifts = drifted(rows, promoted_cores(kb_texts, blocks))
        if args.current:
            drifts = current_drift(drifts, captures)
        if not drifts:
            print(all_clear(args.current))
        elif args.promote:
            sys.stdout.write(promotion_pass(drifts, KB_DIR))
        else:
            sys.stdout.write(render(drift_table(drifts)))
            print("\n" + trailer(len(drifts), args.current))
    else:
        sys.stdout.write(render(inventory_table(rows)))

if __name__ == "__main__":
    main()
