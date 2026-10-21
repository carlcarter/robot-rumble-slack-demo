"""Claude AI stays out of conversations that aren't addressed to it.

In a code channel the bot answers plain follow-ups — but not a question for the
Pit Crew agent, not Pit Crew's own replies, and nothing at all in a stage channel.
"""
import asyncio

from agent import slackcode
from listeners.events import message as message_mod
from listeners.events.message import addressed_elsewhere, from_other_app

ME = "U0CAX2W8FPG"        # Claude AI
PIT_CREW = "U0PITCREW1"   # another app's bot user


def test_question_for_pit_crew_is_not_for_us():
    assert addressed_elsewhere({"text": f"<@{PIT_CREW}> what is the latest telemetry for Edi?"}, ME)


def test_pit_crew_reply_is_not_for_us():
    ev = {"text": "The latest telemetry for Edinburgh (EDI) is stale…", "bot_id": "B0PITCREW"}
    assert from_other_app(ev)
    assert addressed_elsewhere(ev, ME)


def test_plain_human_follow_up_is_still_for_us():
    assert not addressed_elsewhere({"text": "why did you keep the debounce?"}, ME)


def test_mentioning_only_us_is_for_us():
    assert not addressed_elsewhere({"text": f"<@{ME}> patch it"}, ME)


def test_group_mention_is_not_for_us():
    assert addressed_elsewhere({"text": "<!subteam^S123> heads up"}, ME)


class _Ctx:
    def __init__(self, channel):
        self.channel_id = channel
        self.bot_user_id = ME
        self.user_id = "UHUMAN"
        self.team_id = "T0BDW41TXPX"
        self.user_token = None


def _deliver(monkeypatch, channel, event, *, stage):
    calls = []

    async def _not_own(client, ev):
        return False

    async def _is_code(client, ch, **kw):
        return True

    async def _followup(**kw):
        calls.append(kw["text"])

    monkeypatch.setattr(slackcode, "is_own_bot_event", _not_own)
    monkeypatch.setattr(slackcode, "is_code_channel", _is_code)
    monkeypatch.setattr(slackcode, "is_stage_channel", lambda ch: stage)
    monkeypatch.setattr(message_mod._SLACK_CODE_CFG, "enabled", True)
    monkeypatch.setattr(message_mod, "_reply_in_code_channel_followup", _followup)
    asyncio.run(message_mod.handle_message(
        client=None, context=_Ctx(channel), event={"channel_type": "channel", "ts": "1.0", **event},
        logger=__import__("logging").getLogger("t"), say=None, say_stream=None, set_status=None,
    ))
    return calls


def test_code_channel_ignores_pit_crew_question(monkeypatch):
    assert _deliver(monkeypatch, "CCODE", {"text": f"<@{PIT_CREW}> latest telemetry?"}, stage=False) == []


def test_code_channel_ignores_pit_crew_reply(monkeypatch):
    assert _deliver(monkeypatch, "CCODE", {"text": "Telemetry is stale", "bot_id": "B0PIT"}, stage=False) == []


def test_code_channel_still_answers_plain_follow_up(monkeypatch):
    assert _deliver(monkeypatch, "CCODE", {"text": "why the crawl?"}, stage=False) == ["why the crawl?"]


def test_stage_channel_ignores_every_plain_message(monkeypatch):
    assert _deliver(monkeypatch, "CSTAGE", {"text": "why the crawl?"}, stage=True) == []
