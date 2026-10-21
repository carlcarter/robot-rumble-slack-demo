# Robot Rumble Slack Code demo: one-time setup

This sets up the coding agent ("Claude AI") that fixes the robot's code in a Slack Code channel when a red card fires. Do it once, at least a few days before the event. Allow about an hour, plus however long Slack takes to switch on the beta.

**Order matters.** Step 1 can take days and nothing else is any use without it, so start there.

| Step | What | Who | Time |
|---|---|---|---|
| 1 | Request the Slack Code beta | Your Slack contact | Days |
| 2 | Install the Slack CLI and log in | You, Terminal | 10 min |
| 3 | Create the Slack app from the manifest | You, browser | 10 min |
| 4 | Get the two tokens into `tokens.json` | You, browser + editor | 10 min |
| 5 | Link the project to the CLI | You, Terminal | 5 min |
| 6 | Python environment + offline self-test | You, Terminal | 5 min |
| 7 | Model access (no key needed if Claude Code works) | Check only | 2 min |
| 8 | Demo context, channel invites, first run | You, Terminal + Slack | 15 min |

---

## Step 1: Request the Slack Code beta (do this today)

Slack Code ("code channels") is a Slack beta. Without it, the bot still runs, but a coding request gets a normal thread reply instead of a code channel. That isn't the demo.

Ask your Slack contact (or the Slack SE team) to enable it. Give them:

- **Workspace:** Slack Demo 37377, team ID `T0BDW41TXPX` (Enterprise Grid org `E0BE27M820L`)
- **App:** the app ID you'll get in Step 3 (starts `A0…`). If they can enable it at workspace level before the app exists, even better.
- **Features used:** code channels (`agents.conversations.*`), artifact views (diff, Block Kit, canvas), runtime slash commands, streaming.

You'll know it's on when Step 8's test opens a new channel rather than replying in the thread.

---

## Step 2: Install the Slack CLI and log in

The CLI runs the bot locally over Socket Mode. No public URL or server is needed.

**Install** (official script; it puts `slack` in `~/.local/bin`):

```bash
curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash
```

If you already have a different `slack` command, install under an alias instead: `... | bash -s slackcli`, then use `slackcli` everywhere this guide says `slack`.

**Check it:**

```bash
slack version
```

If you get `command not found`, add the folder to your path, then open a new terminal:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Log in to the demo workspace:**

```bash
slack login
```

1. The terminal prints a slash command like `/slackauthticket ABC123…`.
2. In Slack (the **Slack Demo 37377** workspace), paste it into any DM to yourself and send it.
3. A dialog asks you to grant the CLI permissions. Click **Confirm**.
4. A second dialog shows a challenge code. Paste it back into the terminal.

You should see "You've successfully authenticated". The credentials are saved to `~/.slack/credentials.json` (that's your CLI login, not the bot's).

**Check it:**

```bash
slack auth list
```

Note the ID shown for the workspace. On Enterprise Grid you may see the org (`E0BE27M820L`) rather than the workspace (`T0BDW41TXPX`). You need it for `workspace_id` in Step 4.

> If the dialog says an admin must approve the Slack CLI, ask the workspace admin (or your Slack contact from Step 1) to approve it.

---

## Step 3: Create the Slack app from the manifest

1. Go to <https://api.slack.com/apps> and click **Create New App** → **From a manifest**.
2. Pick the **Slack Demo 37377** workspace. On Grid, if it asks, choose the org and grant it to workspace `T0BDW41TXPX`.
3. Paste the contents of `manifest.json` from this folder (JSON tab). Click **Next** → **Create**.
4. On the app's **Basic Information** page, note the **App ID** (`A0…`). Send it to your Slack contact for Step 1.
5. Optional but worth it: under **Display Information**, upload an icon so the bot doesn't show a blank square on stage.

The manifest already asks for everything the demo needs: the code-channel feature, `chat:write.customize` (lets the bot post the reviewer's and safety lead's lines under their names), `canvases:write` (the postmortem), and the events for mentions and code-channel messages.

---

## Step 4: Get the two tokens into `tokens.json`

The bot needs two secrets. **Don't paste them into chat, Slack, or a commit.** Put them straight into the file.

**a) App-level token (`xapp-…`), for Socket Mode:**
Basic Information → **App-Level Tokens** → **Generate Token and Scopes**. Name it `socket`, add the scope `connections:write`, click **Generate**, and copy the token.

**b) Bot token (`xoxb-…`):**
**OAuth & Permissions** → **Install to Workspace** (on Grid: install to the org, then make sure workspace `T0BDW41TXPX` is granted). Approve the scopes, then copy the **Bot User OAuth Token**.

**c) Bot user ID (`U0…`):** in Slack, open the app's profile (search for "Claude AI"), click ⋯ → **Copy member ID**.

**d) Create the file:**

```bash
cd ~/dev/robot-rumble-slack-demo
cp tokens.example.json tokens.json
chmod 600 tokens.json
open -e tokens.json
```

Fill it in like this (IDs are fine to share; the two tokens are not):

```json
{
  "team_id": "T0BDW41TXPX",
  "workspace_id": "<the ID from `slack auth list`>",
  "audit_channel_id": "",
  "bots": {
    "<your App ID, A0…>": {
      "name": "Claude AI",
      "bot_token": "xoxb-…",
      "bot_user_id": "<U0…>",
      "app_token": "xapp-…"
    }
  },
  "users": {}
}
```

The bot refuses to read `tokens.json` unless it's `chmod 600`. `tokens.json` is gitignored.

---

## Step 5: Link the project to the CLI

`run.sh` launches the bot with `slack run`, which needs the project linked to your existing app. Otherwise it would create a second app called "Claude AI (local)" without the code-channel setup.

```bash
cd ~/dev/robot-rumble-slack-demo
slack init
```

- It adds a `.slack/` folder (hooks + config) and may add `slack-cli-hooks` to `requirements.txt`. It's already there, so there should be no change.
- When it asks to **add an existing app**, say yes and pick the App ID from Step 3. If it doesn't ask, run `slack app link` and do the same.
- If it asks whether the manifest source is **local** or **remote**, choose **remote** (the app's settings page is the source of truth; `run.sh` re-applies the code-channel bits on each launch).

`.slack/apps*.json` is gitignored. Commit nothing from `.slack/` except `hooks.json` and `config.json` if you want them shared.

---

## Step 6: Python environment and offline self-test

This folder needs Python 3.12. (The fork was set up with `uv`; plain `python3.12 -m venv` works too.)

```bash
cd ~/dev/robot-rumble-slack-demo
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt pytest-asyncio
.venv/bin/python qa.py --self-test
.venv/bin/python -m pytest -q tests/
```

Expect every line `[PASS]` and exit 0 (327 checks at the time of writing), then all pytest tests passing. One `RuntimeError: boom` line partway through is a deliberate failure test.

---

## Step 7: Model access (the "key" question)

The bot's live replies (the agent's first message in the channel, and any question you ask it) are generated by Claude. **The scripted parts (diffs, replay results, approvals, dashboard, recap) need no model at all.**

You don't need an Anthropic API key if Claude Code already works on this Mac. `run.sh` checks `~/.claude/settings.json`. If it finds the Salesforce Bedrock gateway settings, it uses them; otherwise it uses your `claude` login. Your settings currently point at the gateway.

One setting to make: the template defaults to `claude-haiku-4-5`, which the internal gateway may not serve. Create a `.env` in this folder:

```bash
cat > .env <<'EOF'
SLACK_CODE_ENABLED=1
SLACK_WORKSPACE_TEAM_ID=T0BDW41TXPX
CLAUDE_AI_MODEL=us.anthropic.claude-haiku-4-5-20251001-v1:0
EOF
```

When the bot starts, look for a `model-check:` line in the log. A 401 or "rerouted" there means change `CLAUDE_AI_MODEL` (try `claude-sonnet-5`, which is what Claude Code uses here). If the model fails completely, the demo still runs: the agent falls back to a canned "first pass is in the Code tab" line.

Only if you're **not** on the gateway and have no `claude` login: add `ANTHROPIC_API_KEY=…` to `.env`. Never commit `.env`.

---

## Step 8: Demo context, invites, first run

**a) Give the bot the story** (it's appended to its system prompt):

```bash
cp docs/robot-rumble/demo_context.md personas/_demo_context.md
```

If you change the cast names, change them in three places: `personas/_demo_context.md`, `scenarios/robot_red_card.py` (`PARTICIPANTS` and `participant_beats`), and `channels/seed_robot_red_card.py` (`MESSAGES`).

**b) Invite the bot into the alert channels.** In Slack, in `#rvr-edi-help-me` and `#rvr-lon-help-me`:

```
/invite @Claude AI
```

**c) Start it:**

```bash
./run.sh
```

Leave this terminal open. That's the bot. Wait for "Bolt app is running".

**d) Test run** (on a quiet channel first if you can, then for real):

1. Raise a red card on Edinburgh: drive over the red card, or ask Pit Crew to "send a red card to Edinburgh" and say yes.
2. When the alert lands, seed the team's thread in a **second** terminal:
   ```bash
   .venv/bin/python channels/seed_robot_red_card.py --from-case EDI
   ```
3. In the alert thread, type: `@Claude AI fix the late stop on red cards in line_follower.py`
4. A new channel should open with a diff. If you get a thread reply instead, the Slack Code beta isn't on yet (Step 1).

Then follow [RUNBOOK.md](RUNBOOK.md) for the full run.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Thread reply instead of a new channel | Slack Code beta not enabled for this app | Step 1 |
| `slack run` creates "Claude AI (local)" | Project not linked to your app | Step 5: `slack app link` |
| `PermissionError … tokens.json` | File permissions | `chmod 600 tokens.json` |
| Seed fails with `not_in_channel` | Bot not in the alert channel | `/invite @Claude AI` |
| Reviewer lines show the bot's name | `chat:write.customize` scope missing | Reinstall the app from the manifest |
| Agent's first reply never arrives | Model 401 / timeout | Check `model-check:` in the log; change `CLAUDE_AI_MODEL` |
| A step fires that you didn't mean | A keyword in your message (see the runbook's phrase list) | Stick to the scripted phrases |
