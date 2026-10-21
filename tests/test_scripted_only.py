"""SCRIPTED_ONLY=1: every agent call returns a canned reply and never starts the CLI."""
import asyncio

import pytest

from agent import agent as agent_mod
from scenarios import load_scenario


@pytest.fixture
def scripted(monkeypatch):
    monkeypatch.setenv("SCRIPTED_ONLY", "1")

    class _Boom:
        def __init__(self, *a, **kw):
            raise AssertionError("the Claude CLI must not start in scripted-only mode")
    monkeypatch.setattr(agent_mod, "ClaudeSDKClient", _Boom)


def _ask(text, offloop=False):
    fn = agent_mod.run_agent_offloop if offloop else agent_mod.run_agent
    return asyncio.run(fn(text, with_tools=False))


def test_opening_turn_gets_the_open_reply(scripted):
    reply, session = _ask("You're picking up a coding task…\n\nThe task: fix the late stop on red cards")
    assert reply == load_scenario("robot_red_card").SCRIPTED_REPLIES["open"]
    assert session is None


def test_why_question_answers_from_provenance(scripted):
    reply, _ = _ask("why did you keep the debounce?", offloop=True)
    assert reply == load_scenario("robot_red_card").provenance()["keep_the_debounce"]


def test_only_the_request_is_matched_not_the_context(scripted):
    # A follow-up carries the whole file as context; "deploy" in it must not match.
    reply, _ = _ask("The current file is x. It mentions deploy and config.\n\nRequest: why the crawl?")
    assert reply == load_scenario("robot_red_card").provenance()["crawl_then_confirm"]


def test_unknown_question_gets_the_fallback(scripted):
    reply, _ = _ask("what's the weather in Leith?")
    assert reply == load_scenario("robot_red_card").SCRIPTED_REPLIES["fallback"]


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("SCRIPTED_ONLY", raising=False)
    assert not agent_mod.scripted_only()
