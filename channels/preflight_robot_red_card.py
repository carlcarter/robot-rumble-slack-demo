"""Read-only preflight for the robot_red_card demo. Posts nothing, prints no tokens.

Checks the bot token works, which workspace it's in, the scopes the demo needs,
and that the bot is a member of the alert channels.

Usage (from repo root):
    .venv/bin/python channels/preflight_robot_red_card.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from slack_sdk.errors import SlackApiError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import app_client  # noqa: E402

ALERT_CHANNELS = {"#rvr-edi-help-me": "C0C73EZ4P7G", "#rvr-lon-help-me": "C0C6Z7981JP"}
NEEDED_SCOPES = {"chat:write", "chat:write.customize", "code_channels:manage", "canvases:write",
                 "app_mentions:read", "channels:history"}


def main() -> int:
    client = app_client()
    problems = 0
    try:
        auth = client.auth_test()
    except SlackApiError as e:
        print(f"[FAIL] bot token rejected: {e.response.get('error')}")
        return 1
    print(f"[ OK ] bot token works: user {auth.get('user_id')} in team {auth.get('team_id')} "
          f"({auth.get('url')})")

    granted = set((auth.headers.get("x-oauth-scopes") or "").replace(" ", "").split(",")) - {""}
    missing = NEEDED_SCOPES - granted
    if granted and missing:
        problems += 1
        print(f"[FAIL] missing scopes: {', '.join(sorted(missing))} — reinstall from manifest.json")
    elif granted:
        print("[ OK ] scopes include chat:write.customize, code_channels:manage, canvases:write")
    else:
        print("[ ?? ] couldn't read granted scopes from the response")

    for name, cid in ALERT_CHANNELS.items():
        try:
            info = client.conversations_info(channel=cid)["channel"]
        except SlackApiError as e:
            problems += 1
            print(f"[FAIL] {name} ({cid}): {e.response.get('error')}")
            continue
        if info.get("is_member"):
            print(f"[ OK ] bot is in {name}")
        else:
            problems += 1
            print(f"[FAIL] bot is NOT in {name} — run /invite @Claude AI there")

    print("\nAll good." if not problems else f"\n{problems} problem(s) to fix.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
