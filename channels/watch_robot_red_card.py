"""Read-only: print the red-card alert thread and the newest code channel's messages.

Lets you (or Claude Code) check a live run against docs/robot-rumble/RUNBOOK.md
without screenshots. Posts nothing; uses the bot token, so it only sees channels
the bot is in.

Usage (from repo root):
    .venv/bin/python channels/watch_robot_red_card.py --channel C0C73EZ4P7G --thread-ts 1792497399.296059
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from slack_sdk.errors import SlackApiError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import app_client  # noqa: E402


def _line(m: dict) -> str:
    who = m.get("username") or m.get("user") or m.get("bot_id") or "?"
    text = (m.get("text") or "").replace("\n", " ")
    return f"  [{m.get('ts')}] {who}: {text[:220]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--thread-ts", required=True)
    ap.add_argument("--team-id", default="T0BDW41TXPX", help="Workspace id (Grid needs it).")
    args = ap.parse_args()
    client = app_client()

    print(f"== alert thread {args.channel} / {args.thread_ts}")
    try:
        replies = client.conversations_replies(channel=args.channel, ts=args.thread_ts, limit=50)
        for m in replies.get("messages", []):
            print(_line(m))
    except SlackApiError as e:
        print(f"  error: {e.response.get('error')}")

    # Newest channel the bot is in whose name starts with the code-channel prefix.
    newest = None
    cursor = None
    while True:
        # Enterprise Grid needs the workspace (T…) id here, not the org id.
        page = client.users_conversations(types="public_channel,private_channel", limit=200,
                                          cursor=cursor, team_id=args.team_id)
        for c in page.get("channels", []):
            if c.get("name", "").startswith("claude-") and (newest is None or c["created"] > newest["created"]):
                newest = c
        cursor = page.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    if not newest:
        print("\n== no code channel yet (none named claude-…)")
        return 0
    print(f"\n== code channel #{newest['name']} ({newest['id']})")
    hist = client.conversations_history(channel=newest["id"], limit=50)
    for m in reversed(hist.get("messages", [])):
        print(_line(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
