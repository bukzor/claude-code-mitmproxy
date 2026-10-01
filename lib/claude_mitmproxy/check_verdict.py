"""The normal form every `check_*.py` script takes, and the shared half of it.

A check decomposes into three parts: `collect()` gathers the data, `render()`
formats it for a human, and `PREDICATES` says whether it is healthy. This
module supplies everything downstream of those three -- the verdict block, the
exit status, `--data-only` -- so a check script is its own data and nothing
else, and `monitoring/` can assert the *same* predicate functions the command
prints. The two halves cannot disagree about what healthy means; they differ
only in what they do about it.

A predicate takes the collected data and returns its **evidence**: the
offenders themselves, empty when healthy. Never a bool -- the offenders are
what triage needs, and a predicate that can only say "no" makes every failure
a second investigation.

By convention a predicate's docstring opens with a short sentence naming what
it returns ("fixtures sharing a masked digest."), and explains why that is bad
after it. That first sentence is what the verdict block prints, on pass as
well as fail: a check that silently examined nothing otherwise looks exactly
like one that passed.

Knowing the form, this module also knows who takes it: `all_checks()` is the
inventory, and it is the one every consumer asks rather than keeping its own.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Sequence, TypeVar

Data = TypeVar("Data")

# Not 1: an uncaught traceback already exits 1, so a script that cannot tell
# drift from a crash is a script that will eventually promote a fixture to
# "fix" a NameError.
UNHEALTHY = 2

# `check_*.py` that is deliberately not a check. Only this module: everything
# else matching the glob must take the normal form, and
# `tests/test_all_checks.py` is what says so -- so adding a name here is a
# claim to defend, not a way to quiet a failure.
NOT_A_CHECK = frozenset({"check_verdict"})


def all_checks() -> tuple[ModuleType, ...]:
    """Every check module, in name order.

    Discovered rather than listed. A hand-kept inventory is one more place to
    forget, and it fails in the direction that looks healthy: a check missing
    from it is a check whose properties nothing asserts, and the suite stays
    green saying so. The filesystem already knows which modules there are.

    A function, not a constant, because every check imports this module -- an
    inventory resolved at import time would be a cycle. At call time the
    imports are already cached, so this returns the same module objects a
    caller's own `from claude_mitmproxy import check_masks` would.
    """
    return tuple(
        importlib.import_module(f"{__package__}.{path.stem}")
        for path in sorted(Path(__file__).parent.glob("check_*.py"))
        if path.stem not in NOT_A_CHECK
    )


def summary(predicate: Callable[..., Any]) -> str:
    """The predicate's own first docstring sentence, whitespace-collapsed.
    Sentence, not line: the docstring wraps where the line length says, which
    is nowhere near where the thought ends."""
    doc = " ".join((predicate.__doc__ or predicate.__name__).split())
    return doc.split(". ")[0].rstrip(".")


def lines(evidence: Any) -> list[str]:
    """One line per offender. A mapping's key leads, since the predicates that
    return one are grouping offenders under what they collided on."""
    if isinstance(evidence, dict):
        return [f"{k}: {' '.join(str(v) for v in vs)}" for k, vs in evidence.items()]
    return [str(item) for item in evidence]


def block(findings: dict[Callable[..., Any], Any]) -> str:
    """The verdict: one line per predicate, its evidence indented beneath."""
    out = [f"\n{len(findings)} properties checked:"]
    for predicate, evidence in findings.items():
        out.append(f"{'FAIL' if evidence else '  ok'}  {predicate.__name__} -- {summary(predicate)}")
        out.extend(f"        {line}" for line in lines(evidence))
    return "\n".join(out) + "\n"


def run(
    collect: Callable[[], Data],
    render: Callable[[Data], str],
    predicates: Sequence[Callable[[Data], Any]],
    argv: list[str] | None = None,
) -> int:
    """A check script's whole `main`. Exits `UNHEALTHY` if any predicate found
    something, so `if check-masks; then` reads correctly in a shell.

    `--data-only` suppresses the verdict and always exits 0: it is for diffing
    one run's table against another's, and a judgment nobody asked for has no
    business changing the exit status."""
    argv = sys.argv[1:] if argv is None else argv
    data = collect()
    sys.stdout.write(render(data))
    if "--data-only" in argv:
        return 0
    findings = {predicate: predicate(data) for predicate in predicates}
    sys.stdout.write(block(findings))
    return UNHEALTHY if any(findings.values()) else 0
