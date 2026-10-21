"""Seed for the `robot_red_card` Slack Code scenario (bot-spoofed).

Unlike the other seeds, this one does NOT create a channel or a parent message.
It replies INSIDE the real red-card alert thread that Salesforce posted to the
robot's `-help-me` channel, so the team's discussion sits under the genuine
alert. Each line posts THROUGH THE BOT via chat:write.customize (a name + a
neutral icon) — no per-persona tokens needed.

The seed stops short of the trigger. The presenter types it live in the same
thread (see docs/robot-rumble/RUNBOOK.md):

    @Claude AI fix the late stop on red cards in line_follower.py

Usage (from repo root, after SETUP.md):
    # Pass the alert's channel + thread ts (both on the red Case:
    # Slack_Channel_Id__c and Slack_Message_Ts__c):
    .venv/bin/python channels/seed_robot_red_card.py --channel C0C73EZ4P7G --thread-ts 1792497399.296059

    # Or look up the latest open red Case for a robot via the sf CLI:
    .venv/bin/python channels/seed_robot_red_card.py --from-case EDI --target-org robot-rumble

The bot must be a member of the alert channel: /invite @Claude AI there first.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from slack_sdk.errors import SlackApiError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import app_client  # noqa: E402

# The team in the alert thread. Names match scenarios/robot_red_card.PARTICIPANTS;
# change both together. The presenters (the Edinburgh and London SEs) post their
# own lines live, so they're not scripted here.
MESSAGES = [
    ("Callum Reid",
     "It halted, but it rolled a good hand-width past the card before it stopped. If that card "
     "were a real hazard, the robot would already be on top of it."),
    ("Priya Nair",
     "That's the debounce in `line_follower.py`. Red has to read 3 times in a row before it counts, "
     "and at 0.3 speed that's most of the card gone."),
    ("Morgan Ellis",
     "Telemetry agrees: the frames show it was still at full speed for 3 frames over the red. "
     "I've got yesterday's practice laps if anyone wants a replay."),
    ("Callum Reid",
     "Pit Crew won't touch a red, quite rightly. Can we get a fix in before the next heat?"),
]

_TS_RE = re.compile(r"^\d{9,11}\.\d{6}$")
_CHANNEL_RE = re.compile(r"^[CG][A-Z0-9]{8,}$")
_ROBOT_RE = re.compile(r"^[A-Z]{2,5}$")


def _post(client, channel: str, name: str, text: str, thread_ts: str):
    """Post one line THROUGH THE BOT, spoofing `name` via chat:write.customize."""
    return client.chat_postMessage(
        channel=channel, thread_ts=thread_ts, text=text,
        username=name, icon_emoji=":bust_in_silhouette:",
    )


def _latest_red_case(robot: str, target_org: str) -> tuple[str, str, str]:
    """(case_number, channel_id, thread_ts) of the newest open red Case for `robot`."""
    if not _ROBOT_RE.match(robot):
        sys.exit(f"--from-case expects a robot id like EDI or LON, got {robot!r}")
    sf = shutil.which("sf")
    if not sf:
        sys.exit("The sf CLI isn't on PATH. Pass --channel and --thread-ts instead.")
    soql = (
        "SELECT CaseNumber, Slack_Channel_Id__c, Slack_Message_Ts__c FROM Case "
        f"WHERE Origin = 'Robot' AND Type = 'Robot Critical Issue' AND Robot_ID__c = '{robot}' "
        "AND IsClosed = false AND Slack_Message_Ts__c != null ORDER BY CreatedDate DESC LIMIT 1"
    )
    out = subprocess.run(
        [sf, "data", "query", "--json", "-o", target_org, "-q", soql],
        capture_output=True, text=True, check=False,
    )
    try:
        records = json.loads(out.stdout)["result"]["records"]
    except (ValueError, KeyError):
        sys.exit(f"sf query failed:\n{out.stderr or out.stdout}")
    if not records:
        sys.exit(f"No open red Case with a Slack thread for {robot}. Raise one first "
                 "(drive over the red card, or ask Pit Crew to 'send a red card').")
    r = records[0]
    return r["CaseNumber"], r["Slack_Channel_Id__c"], r["Slack_Message_Ts__c"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed the robot_red_card team thread (bot-spoofed).")
    ap.add_argument("--channel", help="Alert channel id (Case.Slack_Channel_Id__c).")
    ap.add_argument("--thread-ts", help="Alert message ts (Case.Slack_Message_Ts__c).")
    ap.add_argument("--from-case", metavar="ROBOT", help="Look up the latest open red Case for ROBOT (e.g. EDI).")
    ap.add_argument("--target-org", default="robot-rumble", help="sf CLI org alias for --from-case.")
    ap.add_argument("--gap", type=float, default=4.0, help="Seconds between lines (default 4).")
    args = ap.parse_args()

    if args.from_case:
        case_number, channel, thread_ts = _latest_red_case(args.from_case.upper(), args.target_org)
        print(f"[seed] using red Case {case_number} → channel {channel}, thread {thread_ts}")
    else:
        channel, thread_ts = args.channel, args.thread_ts
    if not (channel and thread_ts):
        ap.error("pass --channel and --thread-ts, or --from-case ROBOT")
    if not _CHANNEL_RE.match(channel) or not _TS_RE.match(thread_ts):
        ap.error(f"that doesn't look like a channel id + message ts: {channel!r} {thread_ts!r}")

    client = app_client()
    for i, (name, text) in enumerate(MESSAGES):
        if i:
            time.sleep(args.gap)
        try:
            _post(client, channel, name, text, thread_ts)
        except SlackApiError as e:
            err = e.response.get("error")
            hint = " — /invite @Claude AI into the channel first" if err == "not_in_channel" else ""
            sys.exit(f"[seed] post failed: {err}{hint}")
        print(f"[seed] {name}: posted")

    print("[seed] done. Now type in the same thread:\n"
          "  @Claude AI fix the late stop on red cards in line_follower.py")


if __name__ == "__main__":
    main()
