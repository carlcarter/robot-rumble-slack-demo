"""Stage mode: the story runs IN the presenter's channel and restarts on re-trigger.

No network, no model: a fake Slack client that rejects the code-channel-only
calls (as Slack does for an ordinary channel) and records every post.
"""
import asyncio
import logging

from agent import slackcode
from listeners.events import slack_code
from scenarios import load_scenario

STAGE = "CSTAGE0001"


class _Resp(dict):
    @property
    def data(self):
        return self


class StageClient:
    """An ordinary channel: Slack Code calls fail, normal posts succeed."""

    def __init__(self):
        self.posts = []        # (channel, username or None, text)
        self.created = []      # code channels created (must stay empty)

    async def api_call(self, method, **kw):
        if method == "agents.conversations.create":
            self.created.append(kw)
        return _Resp(ok=False, error="not_agent_channel")

    async def chat_postMessage(self, **kw):
        if kw.get("markdown_text") and kw.get("text"):
            raise RuntimeError("markdown_text_conflict")  # Slack rejects both together
        self.posts.append((kw["channel"], kw.get("username"), kw.get("markdown_text") or kw.get("text", "")))
        return _Resp(ok=True, ts=f"1.{len(self.posts)}", channel=kw["channel"])

    def __getattr__(self, name):
        async def _ok(*a, **kw):
            return _Resp(ok=True, ts="1.0", channel={"id": STAGE, "name": "rr-demo-edi"})
        return _ok


def _patch_fast(monkeypatch):
    monkeypatch.setenv("SLACK_CODE_BEAT_GAP_S", "0")
    monkeypatch.setenv("SLACK_CODE_PREBUILT_DWELL_S", "0")
    monkeypatch.setattr(slack_code, "_pulse_hold_s", lambda action: 0.0)

    async def _no_resolve(client, stem):
        return None
    monkeypatch.setattr(slackcode, "resolve_participant", _no_resolve)

    async def _no_agent(*a, **kw):
        return "", None
    monkeypatch.setattr(slack_code, "run_agent_offloop", _no_agent)


def _trigger(client, ts):
    cfg = slackcode.SlackCodeConfig(enabled=True)
    asyncio.run(slack_code.run_stage_session(
        client=client, logger=logging.getLogger("test"), cfg=cfg,
        task_text="fix the late stop on red cards in line_follower.py",
        channel_id=STAGE, message_ts=ts, user_id="UPRESENTER",
    ))


def test_trigger_runs_in_place_and_creates_no_channel(monkeypatch):
    _patch_fast(monkeypatch)
    client = StageClient()
    _trigger(client, "100.000001")
    assert client.created == []
    assert {ch for ch, _, _ in client.posts} == {STAGE}
    assert slackcode.is_stage_channel(STAGE)
    assert slackcode.get_channel_scenario(STAGE) == "robot_red_card"


def test_diff_falls_back_to_a_message_in_an_ordinary_channel(monkeypatch):
    _patch_fast(monkeypatch)
    client = StageClient()
    _trigger(client, "100.000002")
    diffs = [t for _, who, t in client.posts if who is None and "```diff" in t]
    assert diffs and "needed = 1 if critical" in diffs[0]  # the first-pass diff


def test_backstory_plays_before_the_diff(monkeypatch):
    _patch_fast(monkeypatch)
    client = StageClient()
    _trigger(client, "100.000003")
    arrival = [b["text"] for b in load_scenario("robot_red_card").participant_beats() if b["phase"] == "arrival"]
    texts = [t for _, _, t in client.posts]
    first_diff = next(i for i, (_, who, t) in enumerate(client.posts) if who is None and "```diff" in t)
    arrival_at = [texts.index(t) for t in arrival]
    assert arrival_at == sorted(arrival_at)          # in story order
    assert max(arrival_at) < first_diff              # all before the diff


def test_retrigger_resets_the_story(monkeypatch):
    _patch_fast(monkeypatch)
    client = StageClient()
    _trigger(client, "100.000004")
    slackcode.mark_channel_patched(STAGE)          # run 1 got as far as the patch
    _trigger(client, "100.000005")                 # run 2
    assert not slackcode.is_channel_patched(STAGE)  # the replay will FAIL again


def test_redelivered_trigger_runs_once(monkeypatch):
    _patch_fast(monkeypatch)
    client = StageClient()
    _trigger(client, "100.000006")
    n = len(client.posts)
    _trigger(client, "100.000006")                 # Slack redelivery: same ts
    assert len(client.posts) == n
