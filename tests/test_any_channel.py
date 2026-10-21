"""Scripted hosting works in ANY channel the bot is invited to — no list, and it
survives a restart that wipes the state file (Heroku)."""
from agent import slackcode
from scenarios import route_scenario
from listeners.events.app_mentioned import STAGE_SCENARIOS


def test_trigger_routes_to_the_story_in_any_channel():
    assert route_scenario("fix the late stop on red cards in line_follower.py") in STAGE_SCENARIOS


def test_scripted_mode_treats_every_channel_as_a_stage(monkeypatch):
    monkeypatch.setenv("SCRIPTED_ONLY", "1")
    assert slackcode.is_stage_channel("C0NEWCODECHANNEL")   # never seen before


def test_live_mode_only_knows_channels_it_has_staged(monkeypatch):
    monkeypatch.delenv("SCRIPTED_ONLY", raising=False)
    assert not slackcode.is_stage_channel("C0NEVERSTAGED")


def test_forgotten_channel_falls_back_to_the_scripted_story(monkeypatch):
    # After a restart the per-channel story is gone; the fallback must be the
    # red-card story, not the generator's website default.
    monkeypatch.setenv("SCRIPTED_ONLY", "1")
    monkeypatch.delenv("SLACK_CODE_SCENARIO", raising=False)
    monkeypatch.delenv("SCRIPTED_SCENARIO", raising=False)
    assert slackcode.load_slack_code_config().scenario == "robot_red_card"


def test_live_mode_keeps_the_generator_default(monkeypatch):
    monkeypatch.delenv("SCRIPTED_ONLY", raising=False)
    monkeypatch.delenv("SLACK_CODE_SCENARIO", raising=False)
    assert slackcode.load_slack_code_config().scenario == ""
