"""Incident records carry the build and model they were first seen from."""

from __future__ import annotations

import json

from claude_mitmproxy import incidents
from claude_mitmproxy import prompt_location
from claude_mitmproxy import prompt_patches
from claude_mitmproxy import rule_templates
from claude_mitmproxy import tool_patches


def read_record(capture_dir, rule, digest):
    return json.loads((capture_dir / rule / f"{digest}.json").read_text())


def read_only_record(capture_dir, rule):
    (path,) = (capture_dir / rule).glob("*.json")
    return json.loads(path.read_text())


def write_rule(root, name, match, replace, search=None):
    """A patch directory in the on-disk form `rule_templates.load_rules` reads."""
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "match.md").write_text(match)
    (directory / "replace.md").write_text(replace)
    if search is not None:
        (directory / "search.md").write_text(search)
    return directory


def test_origin_defaults_to_unknown(tmp_path):
    incident = incidents.Incident("some-rule", "some-kind")
    incidents.save_incident(incident, "deadbeef", tmp_path)
    record = read_record(tmp_path, "some-rule", "deadbeef")
    assert record["cc_version"] == "unknown", record
    assert record["model"] == "unknown", record


def test_origin_is_recorded(tmp_path):
    incident = incidents.Incident("some-rule", "some-kind")
    origin = incidents.Origin("2.1.248.abc", "claude-opus-5")
    incidents.save_incident(incident, "deadbeef", tmp_path, origin)
    record = read_record(tmp_path, "some-rule", "deadbeef")
    assert record["cc_version"] == "2.1.248.abc", record
    assert record["model"] == "claude-opus-5", record


def test_origin_is_first_seen_not_latest(tmp_path):
    """The on-disk write is idempotent -- that is what keeps a live proxy from
    rewriting the record on every request -- so a recurring incident keeps the
    origin it was first captured from, exactly as it keeps its `at`."""
    incident = incidents.Incident("some-rule", "some-kind")
    incidents.save_incident(incident, "deadbeef", tmp_path, incidents.Origin("2.1.1", "m1"))
    again = incidents.save_incident(
        incident, "deadbeef", tmp_path, incidents.Origin("2.1.2", "m2")
    )
    assert again is None, again
    record = read_record(tmp_path, "some-rule", "deadbeef")
    assert record["cc_version"] == "2.1.1", record


def test_report_issues_passes_origin_through(tmp_path):
    issues = [incidents.Incident("patch-a", "failed-to-match")]
    origin = incidents.Origin("2.1.250.9de", "claude-fable-5")
    incidents.report_issues("a body", issues, tmp_path, origin)
    digest = incidents.masked_hash("a body")
    record = read_record(tmp_path, "patch-a", digest)
    assert record["cc_version"] == "2.1.250.9de", record


def test_apply_patches_records_origin(tmp_path):
    """A patch that proved itself in scope and then missed its target is the
    commonest incident there is; its record should name the build that drifted."""
    rules_dir = tmp_path / "rules"
    # A separate search is what makes a miss possible: without one it defaults
    # to the match template, which by then has already hit.
    write_rule(rules_dir, "a-patch", "MATCHES", "", search="ABSENT")
    rules = rule_templates.load_rules(rules_dir)

    captures = tmp_path / "captures"
    origin = incidents.Origin("2.1.248.abc", "claude-opus-5")
    prompt_patches.apply_patches("body MATCHES here", rules, captures, origin)
    record = read_only_record(captures, "a-patch")
    assert record["kind"] == "failed-to-match", record
    assert record["cc_version"] == "2.1.248.abc", record


def test_check_strip_floor_records_origin(tmp_path):
    """The `_strip-rate` tripwire fires on wholesale upstream rewrites, so
    which build did the rewriting is exactly the question it raises."""
    captures = tmp_path / "captures"
    origin = incidents.Origin("2.1.249.def", "claude-sonnet-5")
    prompt_patches.check_strip_floor("an unknown shape", "an unknown shape", (), captures, origin)
    record = read_only_record(captures, prompt_patches.STRIP_RULE)
    assert record["kind"].startswith("unknown-shape-"), record
    assert record["cc_version"] == "2.1.249.def", record


def test_apply_tool_patches_records_origin(tmp_path):
    """Tool-description wordings vary by build and model family both, and the
    accepted-upstream file is named for whichever axis varied."""
    patch = tool_patches.ToolPatch("Bash", ("the accepted wording",), "the stub")
    tools = [{"name": "Bash", "description": "a drifted wording"}]
    captures = tmp_path / "captures"
    origin = incidents.Origin("2.1.248.abc", "claude-fable-5")
    tool_patches.apply_tool_patches(tools, {"Bash": patch}, captures, origin)
    record = read_only_record(captures, "tooldesc-Bash")
    assert record["kind"] == "changed-upstream", record
    assert record["cc_version"] == "2.1.248.abc", record
    assert record["model"] == "claude-fable-5", record


def test_cc_version_of_reads_the_billing_header():
    system = [
        {"type": "text", "text": "x-anthropic-billing-header: cc_version=2.1.250.9de; cc_entrypoint=cli;"},
        {"type": "text", "text": "\nYou are an interactive agent"},
    ]
    assert prompt_location.cc_version_of(system) == "2.1.250.9de"


def test_cc_version_of_without_a_header():
    assert prompt_location.cc_version_of([{"type": "text", "text": "no header"}]) == "unknown"
    assert prompt_location.cc_version_of([]) == "unknown"
    assert prompt_location.cc_version_of("a string system") == "unknown"
