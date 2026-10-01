"""`check_inventory`: the checks on disk and the commands that run them
correspond, and every check takes the normal form.

The predicates take an `Inventory`, so the fixtures here are built rather than
imported: nothing has to be a real module on a real path for a planted
violation to be the one the predicate reports.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from claude_mitmproxy import check_inventory


def documented(found):
    """offenders, of which there are none."""
    return []


def fake_check(name: str, *, predicates=(documented,), without: tuple[str, ...] = ()):
    """A module-shaped object. The predicates only ever ask for `__name__`,
    `getattr` and `callable`, so a namespace is as good as an import."""
    attrs = {
        "__name__": f"claude_mitmproxy.{name}",
        "collect": lambda: None,
        "render": lambda found: "",
        "main": lambda argv=None: 0,
        "PREDICATES": predicates,
    }
    for absent in without:
        del attrs[absent]
    return SimpleNamespace(**attrs)


@pytest.fixture
def inventory(tmp_path):
    """A healthy inventory: two checks, a command each, and an exclusion whose
    module is really there."""
    (tmp_path / "check_verdict.py").write_text("the shared half\n")
    return check_inventory.Inventory(
        checks=(fake_check("check_alpha"), fake_check("check_beta")),
        commands={"check_alpha": "x-check-alpha", "check_beta": "x-check-beta"},
        excluded=frozenset({"check_verdict"}),
        package=tmp_path,
    )


def test_a_complete_inventory_is_healthy(inventory):
    assert not any(predicate(inventory) for predicate in check_inventory.PREDICATES)


def test_a_check_nothing_runs(inventory):
    found = inventory._replace(commands={"check_alpha": "x-check-alpha"})
    assert check_inventory.checks_without_a_command(found) == ["check_beta"]


def test_a_command_that_outlived_its_check(inventory):
    found = inventory._replace(commands={**inventory.commands, "check_gone": "x-check-gone"})
    assert check_inventory.commands_without_a_check(found) == ["x-check-gone -> check_gone"]


def test_the_normal_form_is_required_in_full(inventory):
    found = inventory._replace(
        checks=(
            fake_check("check_alpha", without=("render",)),
            fake_check("check_beta", predicates=()),
            fake_check("check_gamma", predicates=("not callable",)),
        )
    )
    assert check_inventory.checks_missing_the_normal_form(found) == {
        "check_alpha": ["render"],
        "check_beta": ["PREDICATES"],
        "check_gamma": ["PREDICATES (not all callable)"],
    }


def test_a_predicate_with_nothing_to_print(inventory):
    def bare(found):
        return []

    found = inventory._replace(checks=(fake_check("check_alpha", predicates=(bare,)),))
    assert check_inventory.predicates_without_a_summary(found) == {"check_alpha": ["bare"]}


def test_an_exclusion_that_lost_its_module(inventory):
    found = inventory._replace(excluded=frozenset({"check_verdict", "check_renamed"}))
    assert check_inventory.excluded_names_that_vanished(found) == ["check_renamed"]


def test_commands_are_keyed_on_the_module_they_import(tmp_path):
    """Tools get console scripts too; only the ones importing a check module
    count, and the command's own spelling is not what links them."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project.scripts]\n"
        'x-check-masks = "claude_mitmproxy.check_masks:main"\n'
        'x-dump-core = "claude_mitmproxy.dump_core:main"\n'
    )
    assert check_inventory.check_commands(pyproject) == {"check_masks": "x-check-masks"}
