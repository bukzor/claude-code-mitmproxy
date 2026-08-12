"""Every `check_*.py` property, asserted -- one test per property, all of them
in one run.

The properties themselves live beside their data, in the check modules, so the
hand-run command and this suite cannot disagree about what healthy means. What
this adds is isolation (one failing property no longer hides the rest) and a
name in a runner. There is nothing check-specific to write here: a new property
is a function in a check module's `PREDICATES`, and it shows up as a test the
next run.

Test ids read `check_masks-dark_masks`, so `pytest -k check_masks` is the one
check and `-k dark_masks` is the one property.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Callable

import pytest

import check_dark_patches
import check_laws
import check_masks
import check_patches
import check_strip_floors
import check_tool_patches
import syscapture
import syspatch
import toolpatch
import verdict

CHECKS = (
    check_masks,
    check_laws,
    check_patches,
    check_dark_patches,
    check_strip_floors,
    check_tool_patches,
)

# What each check needs on disk before its properties mean anything. The checks
# themselves assert instead of skipping -- an absent patch dir is a broken
# environment, and a command that shrugged at one would measure a clean
# zero-strip run. That is right for a hand-run on the machine that proxies, and
# wrong for a checkout that has never run the proxy; that difference is the
# whole of what this table encodes. Absent from it: the checks that read only
# committed fixtures, which are always there.
REQUIRES: dict[Any, tuple[Path, ...]] = {
    check_patches: (syspatch.PATCHES_DIR,),
    check_dark_patches: (syspatch.PATCHES_DIR,),
    check_tool_patches: (toolpatch.PATCHES_DIR,),
    check_strip_floors: (syspatch.PATCHES_DIR, syscapture.PROMPTS_DIR),
}


@functools.cache
def collected(check: Any) -> Any:
    """One `collect()` per check per session: it reads a hundred bodies off
    disk, and every property of a check asks about the same ones."""
    for directory in REQUIRES.get(check, ()):
        if not directory.is_dir() or not any(directory.iterdir()):
            pytest.skip(f"{check.__name__} needs {directory}, which is empty or absent")
    return check.collect()


CASES = [(check, predicate) for check in CHECKS for predicate in check.PREDICATES]


@pytest.mark.parametrize(("check", "predicate"), CASES, ids=lambda o: o.__name__)
def test_check_property(check: Any, predicate: Callable[[Any], Any]):
    evidence = predicate(collected(check))
    assert not evidence, "\n".join(
        [f"{predicate.__name__}: {verdict.summary(predicate)}", *verdict.lines(evidence)]
    )
