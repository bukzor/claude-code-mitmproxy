#!/usr/bin/env python3
"""Offline validation of the check inventory: every `check_*.py` module takes
the normal form, and every one has a command to run it by hand.

A correspondence check, like `check_playbook` -- both sides are in the repo,
so a red means this commit broke something rather than upstream moving. What
it guards is the failure that looks like health: a check whose properties
nothing asserts, or that no operator can run during triage, reports nothing
and so reads exactly like a check that passed.

The inventory itself is `check_verdict.all_checks()`, discovered from the
package rather than listed anywhere. That is what leaves this module only the
question of whether the modules it finds are usable, and it is why there is
nothing here to keep in step with a new check.

Self-referential on purpose: this module is one of the checks it collects, so
it holds itself to the form it demands of the others.

Structure is `check_verdict.py`'s normal form: collect, render, PREDICATES.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, NamedTuple

from claude_mitmproxy import check_verdict
from claude_mitmproxy import repo_paths
from claude_mitmproxy import textfile

PACKAGE_DIR = Path(check_verdict.__file__).parent
PYPROJECT = repo_paths.ROOT / "pyproject.toml"

# The three a check script's `main` is built from. `PREDICATES` is checked
# separately: it is the one that has to be non-empty to mean anything.
NORMAL_FORM = ("collect", "render", "main")


class Inventory(NamedTuple):
    """The checks on disk, the commands claiming to run them, and the package
    the excluded names are supposed to still name."""

    checks: tuple[Any, ...]
    commands: dict[str, str]
    excluded: frozenset[str]
    package: Path


def short(module: Any) -> str:
    """The module's own name, without the package."""
    return module.__name__.rsplit(".", 1)[-1]


def check_commands(pyproject: Path) -> dict[str, str]:
    """Console scripts that run a check, keyed by the module they import.

    Keyed by module rather than command name because the commands spell
    themselves with dashes -- corresponding on the name would test the
    transform instead of the wiring. Scripts pointing anywhere else are tools,
    not checks, and `pyproject.toml` says which is which by saying so.
    """
    scripts = tomllib.loads(textfile.read(pyproject))["project"]["scripts"]
    targets = {name: target.partition(":")[0].rsplit(".", 1)[-1] for name, target in scripts.items()}
    return {module: name for name, module in targets.items() if module.startswith("check_")}


def collect() -> Inventory:
    found = Inventory(
        checks=check_verdict.all_checks(),
        commands=check_commands(PYPROJECT),
        excluded=check_verdict.NOT_A_CHECK,
        package=PACKAGE_DIR,
    )
    assert found.checks, "no checks to check"
    return found


def render(found: Inventory) -> str:
    """The inventory, since its size is the thing a green run is silent
    about."""
    return (
        f"{len(found.checks)} checks, {len(found.commands)} commands,"
        f" {len(found.excluded)} excluded\n"
    )


def checks_without_a_command(found: Inventory) -> list[str]:
    """check modules no console script runs. Every check is also a hand-run
    command: `monitoring/` says whether the repo is healthy, and the command
    is how an operator looks at one check's data while triaging it. A check
    reachable only through pytest is one nobody reaches."""
    return sorted(short(check) for check in found.checks if short(check) not in found.commands)


def commands_without_a_check(found: Inventory) -> list[str]:
    """console scripts naming a check module that is not one. A command left
    behind by a rename or a removal fails at the shell with an import error,
    which reads as a broken install rather than as a stale entry point."""
    names = {short(check) for check in found.checks}
    return sorted(
        f"{command} -> {module}"
        for module, command in found.commands.items()
        if module not in names
    )


def checks_missing_the_normal_form(found: Inventory) -> dict[str, list[str]]:
    """check modules missing part of the normal form, by module. `check_verdict.run`
    calls all three, and `monitoring/` parametrizes over `PREDICATES`; an
    empty one collects no tests, which is indistinguishable from passing."""
    missing: dict[str, list[str]] = {}
    for check in found.checks:
        absent = [name for name in NORMAL_FORM if not callable(getattr(check, name, None))]
        predicates = getattr(check, "PREDICATES", None)
        if not isinstance(predicates, tuple) or not predicates:
            absent.append("PREDICATES")
        elif not all(callable(predicate) for predicate in predicates):
            absent.append("PREDICATES (not all callable)")
        if absent:
            missing[short(check)] = absent
    return missing


def predicates_without_a_summary(found: Inventory) -> dict[str, list[str]]:
    """predicates with no docstring to summarise, by module. The verdict block
    prints each predicate's first docstring sentence on pass as well as fail,
    so one without it leaves a bare function name where the line saying what
    was examined should be."""
    undocumented: dict[str, list[str]] = {}
    for check in found.checks:
        bare = [
            predicate.__name__
            for predicate in getattr(check, "PREDICATES", ())
            if check_verdict.summary(predicate) == predicate.__name__
        ]
        if bare:
            undocumented[short(check)] = bare
    return undocumented


def excluded_names_that_vanished(found: Inventory) -> list[str]:
    """`NOT_A_CHECK` entries naming no module in the package. An exclusion
    outlives the file it excluded after a rename, and then it goes on reading
    as though it holds something out while holding out nothing."""
    return sorted(
        name for name in found.excluded if not (found.package / f"{name}.py").exists()
    )


PREDICATES = (
    checks_without_a_command,
    commands_without_a_check,
    checks_missing_the_normal_form,
    predicates_without_a_summary,
    excluded_names_that_vanished,
)


def main(argv: list[str] | None = None) -> int:
    return check_verdict.run(collect, render, PREDICATES, argv)


if __name__ == "__main__":
    raise SystemExit(main())
