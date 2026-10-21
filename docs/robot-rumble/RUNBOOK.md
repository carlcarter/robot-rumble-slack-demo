# Robot Rumble red card: event-day runbook

**The point:** Agentforce handles the routine. When it's critical, the team comes together, and AI is one of the team, not the boss of it. A coding agent writes the change, a reviewer challenges it, the evidence decides, and a named person signs off. That's maker-checker with AI as the maker.

**Length:** about 5 minutes per run. **Presenters:** one SE per location, each in their own channel, running as many times as they like. Nobody's laptop needs to be on: the bot runs on Heroku in scripted mode, with no Claude login involved.

| Thing | Value |
|---|---|
| Heroku app | `cc-slack-code-channel` |
| Slack app | **Claude AI** (`A0CAH8SFUF9`), bot user `U0CAX2W8FPG` |
| Workspace | Slack Demo 37377 (`T0BDW41TXPX`) |
| Repo / branch | `~/dev/robot-rumble-slack-demo`, branch `robot-rumble` |

---

## Morning: start the bot (one person, about 2 minutes)

Do this once, before the first demo in either city.

**1. Make sure nothing is running on your Mac.** Two copies of the bot sharing one set of tokens split the messages between them at random, and the demo breaks.

```bash
pgrep -fl "python app.py|slack_cli_hooks" || echo "nothing running locally - good"
```

If anything is listed, stop it: press Ctrl+C in its terminal, or `kill <number>`.

**2. Start the worker on Heroku.**

```bash
heroku ps:scale worker=1 -a cc-slack-code-channel
```

**3. Check it's up.** Wait about 20 seconds, then:

```bash
heroku ps -a cc-slack-code-channel
```

You want `worker.1: up` (or `worker-…: up`).

**4. Smoke test in Slack.** In any channel with Claude AI in it, post the trigger (below). You should see Callum's line within a few seconds. Then post the trigger again to reset it for the first audience.

If nothing happens, see **If the bot is silent** at the bottom.

---

## Each demo channel (each SE)

You can use the same channel all day or a fresh one per audience (for example a new Slack Code channel each time). No list to update anywhere.

1. Create the channel, or open a new Slack Code channel.
2. `/invite @Claude AI`
3. Run the demo below.

---

## The demo: what the SE posts

Every message is in your channel, and every one starts with an @mention of **Claude AI**. Type them exactly.

| # | Post this | What the room sees |
|---|---|---|
| 1 | `@Claude AI fix the late stop on red cards in line_follower.py` | Callum (safety) and Priya (engineering) explain the late stop. The agent posts its first-pass diff. Priya: "Not approving it blind. Replay yesterday's laps first." Morgan has the laps ready |
| 2 | `@Claude AI run the track replay` | **FAIL**: 14 false critical stops from glare. Callum: "Not shipping that." Priya suggests slowing down first |
| 3 | `@Claude AI patch it` | Patched diff, replay **PASS**. Priya approves, Callum signs off |
| 4 | `@Claude AI show me the numbers` | Before and after: stop distance 9 cm → 3 cm, 0 false stops |
| 5 | `@Claude AI write the postmortem` | Five-part recap |

**Slow down at step 2.** That's the moment: a person had a hunch, the agent proved it, and nobody shipped a bad fix. Let the fail sit on screen for a breath before anyone speaks.

**Next audience:** post step 1 again, in the same channel or a new one. The story resets and the replay fails again.

**Optional Q&A,** any time after step 1. These get a pre-written answer in a thread:

- `@Claude AI why did you keep the debounce?`
- `@Claude AI why the crawl?`
- `@Claude AI who approves this?`
- `@Claude AI is this deployed to the robot?`

Anything else gets a polite "I can run the replay, patch it, show the numbers or write the postmortem".

**Pit Crew in the same channel is fine.** Claude AI ignores messages to Robot Rumble Pit Crew and Pit Crew's replies. Pit Crew's answers arrive as "Only visible to you": click **Share in Thread** so the room sees them.

### Typing rules

Steps fire on **keywords** inside an @mention of Claude AI. Plain messages (no @mention) are ignored completely, so chat freely. But inside an @mention, keep these words out of anything except the scripted step:

| Step | Trigger words |
|---|---|
| Replay | "check", "verify", "replay", "stable", "lock" |
| Patch | "patch", "fix it", " fix " |
| Numbers | "dashboard", "metrics", "the numbers" |
| Recap | "recap", "deck", "slides", "leadership", "postmortem" |

---

## What to say (spoken, not read)

**Before step 1:** "Yellow and green, our Pit Crew agent fixes on its own. Red it hands to us. That's deliberate: critical stays with a person. So let's get the team together."

**Step 1, as the team chimes in:** "Everyone who needs to be here is already here. The engineer who knows the code, the person who owns safety, the data. And the agent's already taken a first pass."

**Step 2, after the fail:** "That's the reviewer earning their keep. The first fix stopped sooner, and it would have flooded us with false alarms. In a bank, that's the fraud rule that blocks every genuine customer."

**Step 3, after sign-off:** "Soft stop, then hard stop. Slow down on suspicion, halt on confirmation. Same pattern as a soft hold on a suspicious payment. And look who approved it: a named reviewer and a named owner, with the evidence in the channel."

**Closing:** "Agentforce runs the routine. Slack is where the team comes together for the critical. And every decision, every review and every approval is written down."

### Be upfront about what's staged

The Slack workflow, the channel and the robot are real. **The team's lines and the code change are pre-written** so it runs the same every time, and **the robot's code doesn't change** during the demo. Both diffs are genuine changes to the robot's real code, with passing tests, so anyone who checks the repo will find matching code. If a bank architect asks: "The workflow's real, the conversation is scripted for the stage, and here's the real diff." Hiding it is what would cost you credibility.

---

## Evening: stop the bot (after the last city finishes)

Edinburgh runs longer, so wait for them.

```bash
heroku ps:scale worker=0 -a cc-slack-code-channel
heroku ps -a cc-slack-code-channel        # "No dynos" = stopped
```

Stopping it saves dyno hours. Nothing is lost: the bot keeps no data you need.

---

## If the bot is silent

Work down the list:

1. **Is it running?** `heroku ps -a cc-slack-code-channel`. If it says "No dynos", run the morning step 2 again.
2. **Is a second copy running?** Check your Mac (morning step 1). Also make sure nobody else is running `./run.sh` with the same tokens.
3. **Is the bot in the channel?** `/invite @Claude AI`.
4. **Did you @mention the right app?** It must be **Claude AI**. Not "Claude AI (local)" and not "Claude".
5. **What do the logs say?**
   ```bash
   heroku logs --tail -a cc-slack-code-channel
   ```
   Post the trigger while watching. You want `app_mention IN:` then `stage trigger → robot_red_card (in place)`. No `app_mention IN:` at all means Slack isn't delivering to this process (go back to 2 and 4).
6. **Restart it:** `heroku ps:restart -a cc-slack-code-channel`, wait 20 seconds, then post the trigger again.

**A run stuck partway?** Post the trigger again. That always resets it.

**Heroku restarted the worker mid-run?** Heroku restarts workers about once a day. You lose that run's progress (the replay fails again), so post the trigger again. Every other channel carries on.

---

## Changing the story

Everything on screen comes from `scenarios/robot_red_card.py`:

| What | Where |
|---|---|
| Replay numbers (9 cm, 14 false stops…) | `REPLAY` |
| The team's lines | `participant_beats()` |
| The agent's own sentences and Q&A answers | `SCRIPTED_REPLIES` |
| Cast names | `PARTICIPANTS` (also update `participant_beats()`) |

After editing:

```bash
cd ~/dev/robot-rumble-slack-demo
.venv/bin/python qa.py --self-test && .venv/bin/python -m pytest -q tests/
git commit -am "Update the red-card story"
git push heroku robot-rumble:main         # Heroku rebuilds and restarts the bot
```

Before the event, swap the illustrative replay numbers for figures from a real practice run (Data 360 has the telemetry).

---

## Heroku config (reference)

Already set on `cc-slack-code-channel`. Only needed if you rebuild the app or rotate the Slack tokens:

```bash
heroku config:set -a cc-slack-code-channel \
  SLACK_BOT_TOKEN='xoxb-…' SLACK_APP_TOKEN='xapp-…' \
  SCRIPTED_ONLY=1 SCRIPTED_SCENARIO=robot_red_card \
  SLACK_CODE_ENABLED=1 SLACK_WORKSPACE_TEAM_ID=T0BDW41TXPX \
  LOG_LEVEL=INFO
```

The two tokens are secrets: copy them from `tokens.json` or the app's settings at api.slack.com, never into chat. Changing a config var restarts the worker automatically.

**Live mode** (the agent writing its own replies through your Claude Code login) isn't used for the event. It runs only on your Mac with `SCRIPTED_ONLY=` blank in `.env`, and still needs locking down before it's demo-safe. See SETUP.md.
