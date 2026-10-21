"""Read-only preflight for the robot_red_card demo. Posts nothing, prints no tokens.

Checks the bot token works, which workspace it's in, and that the app has the
scopes the demo needs. Run it on your Mac (it reads tokens.json) before an
event, or after rotating the app's tokens.

Usage (from repo root):
    .venv/bin/python channels/preflight_robot_red_card.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from slack_sdk.errors import SlackApiError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import app_client  # noqa: E402

NEEDED_SCOPES = {"chat:write", "chat:write.customize", "code_channels:manage", "canvases:write",
                 "app_mentions:read", "channels:history"}


def main() -> int:
    client = app_client()
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
        print(f"[FAIL] missing scopes: {', '.join(sorted(missing))} — reinstall from manifest.json")
        return 1
    if granted:
        print("[ OK ] scopes include chat:write.customize, code_channels:manage, canvases:write")
    else:
        print("[ ?? ] couldn't read granted scopes from the response")
    print("\nAll good. Invite @Claude AI into each demo channel before the first run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
