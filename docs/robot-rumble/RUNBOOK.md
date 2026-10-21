# Robot Rumble red card: demo runbook

**The point:** Agentforce handles the routine. When it's critical, the team comes together, and AI is one of the team, not the boss of it. A coding agent writes the change, a reviewer challenges it, the evidence decides, and a named person signs off. That's maker-checker with AI as the maker.

**Length:** about 5 minutes. **Presenter:** one SE per location, each running it independently in their own channel. No help-me channels and no hand-offs between Edinburgh and London.

## Two modes

| | **Scripted** (`SCRIPTED_ONLY=1` in `.env`) | **Live** (`SCRIPTED_ONLY=` blank) |
|---|---|---|
| Agent's replies | Pre-written (`SCRIPTED_REPLIES` in `scenarios/robot_red_card.py`) | Your local Claude Code login |
| Needs | Python + `tokens.json`. Nothing else | Your Mac, your gateway sign-in |
| Can host on | Anything always-on: a server, a Pi, a spare Mac | Your Mac only |
| Unscripted questions | A pre-written answer if the question matches; otherwise a polite "I can do the runbook steps" | Real answers; can build new things |
| Same story on screen? | Yes. Every step in the table below is identical in both modes | Yes |

The scripted steps (diff, replay, patch, numbers, recap, the team's lines) never use the model in either mode. The mode only changes the agent's own sentences. `run.sh` prints which mode it's in when it starts.

## One-time setup (per presenter)

1. In Slack, create your own channel, e.g. `#rr-demo-edi` (or open a Slack Code channel if you have one).
2. `/invite @Claude AI` into it.
3. That's it. The channel becomes your stage the first time you post the trigger, and stays one after bot restarts.

## Before each session

- [ ] `./run.sh` running in a terminal ("Bolt app is running")
- [ ] `personas/_demo_context.md` in place (`cp docs/robot-rumble/demo_context.md personas/_demo_context.md`)
- [ ] Your channel on the big screen

## The run (every message is in your channel, every one is an @mention)

| # | Type | What the room sees |
|---|---|---|
| 1 | `@Claude AI fix the late stop on red cards in line_follower.py` | The safety lead and the robotics engineer explain the late stop. The agent posts its first-pass diff. The reviewer: "Not approving it blind. Replay yesterday's laps first." |
| 2 | `@Claude AI run the track replay` | **FAIL**: 14 false critical stops from glare. The safety lead: "Not shipping that." |
| 3 | `@Claude AI patch it` | Patched diff, replay **PASS**. Reviewer approves, safety lead signs off |
| 4 | `@Claude AI show me the numbers` | Before/after: stop distance 9 cm → 3 cm, 0 false stops |
| 5 | `@Claude AI write the postmortem` | Recap, 5 sections |

**Running it again:** post step 1 again in the same channel. The story resets (the replay fails again, a fresh agent conversation) and plays from the top. Do this as many times as you like through the day. Scroll or clear the channel between audiences if you want a clean screen; the bot doesn't care.

**Only @mentions do anything.** Plain messages in your channel are ignored, so you can chat or paste notes freely. An @mention that isn't one of the five phrases gets a normal answer in a thread (good for "@Claude AI why did you keep the debounce?").

**In an ordinary channel** the diff, numbers and recap arrive as messages. **In a Slack Code channel** they also appear as Code/Dashboard/Recap tabs.

**Slow down at step 2.** That's the moment: a person had a hunch, the agent proved it, and nobody shipped a bad fix. Let the fail verdict sit on screen for a breath before anyone speaks.

## What to say (spoken, not read)

**Before step 1 (setting it up):** "Yellow and green, our Pit Crew agent fixes on its own. Red it hands to us. That's deliberate: critical stays with a person. So let's get the team together."

**Step 1, as the team chimes in:** "Everyone who needs to be here is already here. The engineer who knows the code, the person who owns safety, the data. And the agent's already taken a first pass."

**Step 2, after the fail:** "That's the reviewer earning their keep. The first fix stopped sooner, and it would have flooded us with false alarms. In a bank, that's the fraud rule that blocks every genuine customer."

**Step 3, after sign-off:** "Soft stop, then hard stop. Slow down on suspicion, halt on confirmation. Same pattern as a soft hold on a suspicious payment. And look who approved it: a named reviewer and a named owner, with the evidence in the channel."

**Closing:** "Agentforce runs the routine. Slack is where the team comes together for the critical. And every decision, every review and every approval is written down."

## Typing rules (important)

Steps fire on **keywords** in an @mention, not intent. Stick to the five phrases above. Inside an @mention, these words trigger a step, so keep them out of anything else you ask the bot:

| Want | Type | Avoid in other messages |
|---|---|---|
| Replay | `run the track replay` | "check", "verify", "replay", "stable", "lock" |
| Patch | `patch it` | "patch", "fix it", " fix " |
| Numbers | `show me the numbers` | "dashboard", "metrics" |
| Recap | `write the postmortem` | "recap", "deck", "slides", "leadership" |

Any other @mention goes to the live model, which is slower and unscripted. Fine for a Q&A moment ("why did you keep the debounce?" answers from recorded reasoning), but keep it out of the main run.

## Be upfront about what's staged

The Slack Code workflow, the channel, the people and the robot are real. **The code change is pre-written** so it works the same every time on stage, and **the robot's code doesn't change** during the demo. Both diffs are genuine changes to the robot's real code, with passing tests, so anyone who checks the repo will find matching code. If a bank architect asks, say so: "The workflow's live, the change is scripted for the stage, and here's the real diff." Hiding it is what would cost you credibility.

## Before the event

- [ ] Replace the replay numbers in `scenarios/robot_red_card.py` (`REPLAY`) with figures from a real practice run. Data 360 has the telemetry. Then re-run `qa.py --self-test`.
- [ ] Swap the fictional cast names for real colleagues if they're happy to be named (three files, see SETUP.md Step 8a).
- [ ] Decide whether the robot should actually get the patch after the event. The patched code is in `scenarios/robot_red_card.py` and passes the robot's test suite.

## Resetting between runs

- Nothing to do. Post the trigger again and the story restarts in the same channel.
- Restarting `./run.sh` mid-day is safe: your channel stays a stage channel.
- If a run gets stuck partway, post the trigger again. That always resets it.
