"""The robot_red_card review loop: the right people speak after each scripted beat.

Drives check (fail) → patch → check (pass) → recap against a fake Slack client
and asserts the spoofed chime-ins land in story order. No network, no model.
"""
import asyncio
import logging

from agent import slackcode
from listeners.events import slack_code
from scenarios import load_scenario

CHANNEL = "CREVIEWLOOP"


class _FakeResp(dict):
    ok = True

    @property
    def data(self):
        return self


class FakeClient:
    """Records spoofed chime-ins; answers every other Slack call with ok."""

    def __init__(self):
        self.chimes = []

    async def chat_postMessage(self, **kw):
        if kw.get("username"):
            self.chimes.append((kw["username"], kw.get("text", "")))
        return _FakeResp(ok=True, ts="1.0", channel=CHANNEL)

    async def api_call(self, *a, **kw):
        return _FakeResp(ok=True)

    def __getattr__(self, name):
        async def _ok(*a, **kw):
            return _FakeResp(ok=True, ts="1.0", channel={"id": CHANNEL, "name": "claude-fix-late-stop"})
        return _ok


def _run_loop(monkeypatch):
    monkeypatch.setenv("SLACK_CODE_BEAT_GAP_S", "0")
    monkeypatch.setattr(slack_code, "_pulse_hold_s", lambda action: 0.0)

    async def _no_resolve(client, stem):
        return None
    monkeypatch.setattr(slackcode, "resolve_participant", _no_resolve)

    cfg = slackcode.SlackCodeConfig(enabled=True)
    slackcode.set_channel_scenario(CHANNEL, "robot_red_card")
    slackcode.clear_channel_patched(CHANNEL)
    slackcode.clear_session_stopped(CHANNEL)
    client = FakeClient()
    log = logging.getLogger("test")

    async def go():
        marks = {}
        await slack_code.run_durability_check(client, log, cfg, CHANNEL)
        marks["after_fail"] = len(client.chimes)
        await slack_code.run_patch(client, log, cfg, CHANNEL)
        marks["after_patch"] = len(client.chimes)
        await slack_code.run_durability_check(client, log, cfg, CHANNEL)
        marks["after_pass"] = len(client.chimes)
        await slack_code.run_make_recap(client, log, cfg, CHANNEL)
        return marks

    marks = asyncio.run(go())
    return client.chimes, marks


def _expected(phase):
    return [(b["name"], b["text"]) for b in load_scenario("robot_red_card").participant_beats()
            if b["phase"] == phase]


def test_each_beat_fires_its_own_people_in_order(monkeypatch):
    chimes, marks = _run_loop(monkeypatch)
    assert chimes[:marks["after_fail"]] == _expected("on_check_fail")
    assert chimes[marks["after_fail"]:marks["after_patch"]] == _expected("on_patch")
    assert chimes[marks["after_patch"]:marks["after_pass"]] == _expected("on_check_pass")
    assert chimes[marks["after_pass"]:] == _expected("on_recap")


def test_approval_follows_the_patch_not_the_failed_check(monkeypatch):
    chimes, marks = _run_loop(monkeypatch)
    failed_check_lines = " ".join(t for _, t in chimes[:marks["after_fail"]])
    assert "Approved" not in failed_check_lines
    approvals = [n for n, t in chimes[marks["after_fail"]:marks["after_patch"]] if "Approved" in t]
    assert approvals == ["Priya Nair", "Callum Reid"]  # reviewer, then sign-off


def test_beat_phases_cover_every_scenario_beat():
    for slug in ("robot_red_card", "checkout_incident", "website_redesign"):
        for b in load_scenario(slug).participant_beats():
            assert b["phase"] in slack_code.BEAT_PHASES
