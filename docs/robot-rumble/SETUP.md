# Robot Rumble Slack Code demo: setup

How the red-card coding agent ("Claude AI") is built and hosted. **For event day, use [RUNBOOK.md](RUNBOOK.md)** — this file is for rebuilding from scratch or changing the setup.

## How it fits together

- **The bot** is this repo: a Python Slack app (Bolt, Socket Mode). It connects out to Slack, so it needs no public URL.
- **The story** is `scenarios/robot_red_card.py`: diffs, replay results, the team's lines, the agent's replies. Both diffs are real changes to the robot's `line_follower.py` with passing tests.
- **Scripted mode** (`SCRIPTED_ONLY=1`) is how the event runs. Every reply is pre-written, so the bot needs only its two Slack tokens. No Claude login, no Slack CLI.
- **Hosting:** Heroku app `cc-slack-code-channel`, one worker dyno.
- **Channels:** any channel the bot is invited to. A presenter @mentions it with the trigger and the story runs in that channel.

## Already done (Slack Demo 37377)

| | |
|---|---|
| Slack app | **Claude AI**, app ID `A0CAH8SFUF9`, bot user `U0CAX2W8FPG`, created from `manifest.json` |
| Slack Code | Enabled for the app (code channels work) |
| Tokens | Bot token (`xoxb-`) and app-level token (`xapp-`, scope `connections:write`) in `tokens.json` on Carl's Mac and in Heroku config vars |
| Heroku | `cc-slack-code-channel`, git remote `heroku`, deploys branch `robot-rumble` |

Two other bots in the workspace are **not** this one: "Claude AI (local)" (`A0CB2R432LU`, made by `slack run`; safe to delete) and "Claude" (`A0BL32EUK0D`, an older app). Only invite **Claude AI**.

---

## Rebuilding from scratch

### 1. The Slack app

1. <https://api.slack.com/apps> → **Create New App** → **From a manifest** → Slack Demo 37377 (on Grid, grant it to workspace `T0BDW41TXPX`) → paste `manifest.json`.
2. **Basic Information → App-Level Tokens** → generate one named `socket` with scope `connections:write`. That's the `xapp-` token.
3. **OAuth & Permissions → Install to Workspace**. Copy the **Bot User OAuth Token** (`xoxb-`).
4. Ask your Slack contact to enable **Slack Code** for the new app ID. Without it the demo still runs in ordinary channels (diffs arrive as messages), but Slack Code channels and their tabs won't work.

The tokens are secrets: put them straight into `tokens.json` or Heroku, never into chat or a commit.

### 2. Local environment (to test or edit the story)

```bash
cd ~/dev/robot-rumble-slack-demo
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt pytest-asyncio
cp tokens.example.json tokens.json && chmod 600 tokens.json   # then fill in the IDs and tokens
.venv/bin/python qa.py --self-test && .venv/bin/python -m pytest -q tests/
.venv/bin/python channels/preflight_robot_red_card.py          # checks the tokens and scopes, posts nothing
```

`tokens.json` shape (IDs are fine to share; the two tokens are not):

```json
{
  "team_id": "T0BDW41TXPX",
  "workspace_id": "E0BE27M820L",
  "audit_channel_id": "",
  "bots": {
    "A0CAH8SFUF9": {
      "name": "Claude AI",
      "bot_token": "xoxb-…",
      "bot_user_id": "U0CAX2W8FPG",
      "app_token": "xapp-…"
    }
  },
  "users": {}
}
```

Local `.env` for scripted mode:

```
SCRIPTED_ONLY=1
SCRIPTED_SCENARIO=robot_red_card
SLACK_CODE_ENABLED=1
SLACK_WORKSPACE_TEAM_ID=T0BDW41TXPX
```

Run it locally with `./run.sh`. It reads `tokens.json` and `.env` and prints `SCRIPTED_ONLY: no model, no Claude login`. **Never run it locally while Heroku is running.** Two copies with the same tokens split the messages between them and the demo breaks.

### 3. Heroku

```bash
cd ~/dev/robot-rumble-slack-demo
heroku login
heroku create cc-slack-code-channel            # or: heroku git:remote -a cc-slack-code-channel
heroku config:set -a cc-slack-code-channel \
  SLACK_BOT_TOKEN='xoxb-…' SLACK_APP_TOKEN='xapp-…' \
  SCRIPTED_ONLY=1 SCRIPTED_SCENARIO=robot_red_card \
  SLACK_CODE_ENABLED=1 SLACK_WORKSPACE_TEAM_ID=T0BDW41TXPX \
  LOG_LEVEL=INFO
git push heroku robot-rumble:main
heroku ps:scale worker=1 -a cc-slack-code-channel
```

What Heroku uses from the repo:
- `Procfile`: `worker: python app.py`. A worker only, no web dyno.
- `.python-version`: `3.12`.
- `requirements.txt`: dependencies.

`run.sh`, `tokens.json` and `.env` aren't used on Heroku. The bot reads its config vars instead.

**Dyno type:** a worker-only app never sleeps. Eco covers about 720 of its shared 1,000 hours a month if left running. Basic is the dependable choice for an event day. Scale to 0 in the evening to save hours.

**Restarts:** Heroku restarts the worker about once a day and wipes its disk. The bot copes: in scripted mode every channel is a demo channel, and a forgotten story falls back to the red card. A restart mid-run just means re-posting the trigger.

---

## Live mode (not used for the event)

With `SCRIPTED_ONLY=` blank in `.env`, `./run.sh` on Carl's Mac sends the agent's own sentences to Claude through his Claude Code login, so it can answer anything and build new things. The scripted steps are the same in both modes.

**Not demo-safe yet.** The live agent currently runs with every tool and no permission prompts, as Carl's user. That's how it opened a real PR on `robot-rumble-pi` (since closed). Before using it again it needs:

- A temporary copy of `robot-rumble-pi-public` to work in.
- Tools limited to file edits in that copy, plus `git` and `gh`.
- A fine-grained GitHub token limited to that repo.
- Only named people allowed to drive it.
- A fresh branch per run, plus a clean-up script for old PRs.

Until then, don't run live mode where others can @mention the bot.

How live mode signs in: `run.sh` exports the `env` block from `~/.claude/settings.json`, and the bot passes only the `apiKeyHelper` setting to the `claude` CLI. Your gateway sign-in has to be working, and you can check it by running `claude -p hi`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No reply at all | Worker not running, or a second copy running | RUNBOOK → If the bot is silent |
| Replies in a thread, no story | `SLACK_CODE_ENABLED` not set | Set it in Heroku config or `.env` |
| Reviewer lines show the bot's name | `chat:write.customize` scope missing | Reinstall the app from `manifest.json` |
| "Not logged in · Please run /login" | Live mode without a working gateway sign-in | Use scripted mode, or check `claude -p hi` works |
| Diff missing in an ordinary channel | Slack rejected the message | Check `heroku logs` for "stage diff fallback post failed" |
| A step fires that you didn't mean | A trigger word in your @mention | RUNBOOK → Typing rules |
