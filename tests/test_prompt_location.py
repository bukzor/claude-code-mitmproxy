from claude_mitmproxy import prompt_location

# The v2.1.327 opening, verbatim from a live request.
V2_1_327_OPENING = (
    "\nYou are an agent working with the user toward their goals,"
    " using your own judgment along the way.\n"
)


def test_locates_the_v2_1_327_opening():
    body = {"type": "text", "text": V2_1_327_OPENING}
    system = [
        {"type": "text", "text": "x-anthropic-billing-header: cc_version=2.1.327.fda; cc_entrypoint=cli;"},
        {"type": "text", "text": "You are Claude Code, Anthropic's official CLI for Claude."},
        body,
    ]
    assert prompt_location.locate_prompt_bodies(system) == [body]


def test_string_system_with_the_v2_1_327_opening_carries_a_body():
    assert prompt_location.carries_body_marker("preamble" + V2_1_327_OPENING)


def test_text_without_any_opening_carries_no_body():
    assert not prompt_location.carries_body_marker("\nYou are a security monitor")
