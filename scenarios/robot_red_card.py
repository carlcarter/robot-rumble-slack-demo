"""Scenario: Robot Rumble red card — the Edinburgh robot stops too late (carlcarter/robot-rumble-pi-public).

The Robot Rumble story, for a banking / exec audience: Agentforce handles the
routine, people own the critical. The robot hits a red card and halts — but only
after rolling well past the card's edge. Pit Crew (by design) won't resolve a red.

Stage mode (how it runs on the day): one presenter creates their own channel,
invites the bot, and posts

    @Claude AI fix the late stop on red cards in line_follower.py

The whole session then runs IN that channel (see slack_code.run_stage_session):
the team's backstory plays as the "arrival" beats, then the first-pass diff, and
the presenter drives the rest with @mentions. Posting the trigger again restarts
the story in the same channel. (In a normal channel without stage mode, the same
trigger opens a new code channel instead.) This module is the SINGLE source of
truth for every artifact the session shows.

Beats (a maker-checker review loop, not a feature tour):
  - first pass                 → the Code diff (halt on the FIRST red read)
  - reviewer doubts it         → on_artifacts: "replay yesterday's laps first"
  - "run the track replay"     → a replay that FAILS on a real flaw
  - safety lead refuses        → on_check_fail
  - "patch it"                 → crawl on suspicion, halt on confirmation; PASSES
  - reviewer + owner approve   → on_patch
  - "show me the numbers"      → the stop-distance / false-stop dashboard
  - "write the postmortem"     → a 5-section recap canvas

The authored flaw (the demo's peak, and it is real — both diffs are genuine
changes to robot-rumble-code with passing tests): the base diff makes red halt
on the first colour read. It stops sooner, but a single-frame red read (the tape
seam under stand lighting) now raises a critical Case. The debounce was never
the bug; it was doing its job at full speed. The patch keeps the debounce and
instead drops to a crawl on the first red read, so the robot is nearly stopped
by the time the halt is confirmed.

The replay NUMBERS (REPLAY below) are illustrative. Before the event, replace
them with figures from a real practice run (Data 360 has the telemetry).
"""
from __future__ import annotations

# --- Identity / context-bar facts --------------------------------------------
SLUG = "robot_red_card"
REPO = "carlcarter/robot-rumble-pi-public"
REPO_URL = "https://github.com/carlcarter/robot-rumble-pi-public"
BRANCH_PREFIX = "fix/"
# Stage mode (the presenter's own channel): one fixed branch for every run.
STAGE_BRANCH = "fix/red-card-late-stop"
# No real PR exists, so point the chip at the repo's pull-request list rather
# than a numbered PR that would 404. (_pr_label shows "PR (draft)".)
PR_URL = f"{REPO_URL}/pulls"

# The check this scenario runs → /check-track-replay + the context-bar pass item.
CHECK_LABEL = "track-replay"

# Diff only. No Preview: a preview makes the engine treat the session as a live
# HTML artifact and replace the Python diff. The Dashboard is published on demand
# by the metrics beat ("show me the numbers") so it doesn't spoil the outcome
# when the channel opens.
ARTIFACTS = {"diff"}


# --- The replay numbers: ONE source for the reports, dashboard and recap -------
REPLAY = {
    "laps": 120,                 # practice laps replayed
    "source": "Edinburgh practice laps, 20 Oct, from Data 360 telemetry",
    "stop_cm_before": 9,         # cm past the red card's edge, original code
    "stop_cm_draft": 2,          # first pass (halt on first read)
    "stop_cm_after": 3,          # patched (crawl, then confirmed halt)
    "glare_frames": 14,          # single-frame red reads that are NOT a red card
    "false_stops_draft": 14,     # each one a critical Case + Slack alert
    "false_stops_after": 0,
    "tests_passed": 50,          # line_follower + control_loop suites, patched
}


# --- Code tab: the diff (pre-patch and post-patch) ---------------------------
_DRAFT_DIFF = r'''diff --git a/line_follower.py b/line_follower.py
--- a/line_follower.py
+++ b/line_follower.py
@@ -44,6 +44,9 @@ DEFAULT_CONFIG = {
     "search_step": 3.0,           # degrees added to the sweep each lost tick
     "patch_confirm_samples": 3,   # consecutive patch reads before it counts
     "reacquire_samples": 5,       # consecutive line reads to re-arm after resume
+    # Critical colours halt on the FIRST read: stopping ~10 cm late on a red
+    # hazard is worse than any debounce saving. Other colours keep the confirm.
+    "critical_colours": ["red"],
 }
 
 
@@ -151,7 +154,9 @@ class LineFollower:
                 self._patch_run_colour = colour
                 self._patch_run = 1
 
-            if self._patch_run >= self._config["patch_confirm_samples"]:
+            critical = colour in self._config["critical_colours"]
+            needed = 1 if critical else self._config["patch_confirm_samples"]
+            if self._patch_run >= needed:
                 self._state = ISSUE
                 self._patch_run = 0
                 self._patch_run_colour = None
diff --git a/tests/test_line_follower.py b/tests/test_line_follower.py
--- a/tests/test_line_follower.py
+++ b/tests/test_line_follower.py
@@ -71,29 +71,29 @@ def test_configurable_line_colour():
 
 def test_patch_requires_confirm_samples():
     f = make_follower()
-    assert f.detect_issue(FakeTel("red")) is None   # 1
-    assert f.detect_issue(FakeTel("red")) is None   # 2
-    issue = f.detect_issue(FakeTel("red"))          # 3 → fires
+    assert f.detect_issue(FakeTel("yellow")) is None   # 1
+    assert f.detect_issue(FakeTel("yellow")) is None   # 2
+    issue = f.detect_issue(FakeTel("yellow"))          # 3 → fires
     assert issue is not None
-    assert issue["hazard"] == "red_card"
-    assert issue["colour"] == "red"
+    assert issue["hazard"] == "yellow_card"
+    assert issue["colour"] == "yellow"
     assert f.state == ISSUE
 
 
 def test_patch_run_breaks_on_non_patch_colour():
     f = make_follower()
-    f.detect_issue(FakeTel("red"))
-    f.detect_issue(FakeTel("red"))
+    f.detect_issue(FakeTel("yellow"))
+    f.detect_issue(FakeTel("yellow"))
     f.detect_issue(FakeTel("blue"))  # breaks the run
-    assert f.detect_issue(FakeTel("red")) is None  # count restarted
+    assert f.detect_issue(FakeTel("yellow")) is None  # count restarted
     assert f.state == FOLLOWING
 
 
 def test_flicker_between_patch_colours_does_not_confirm():
     f = make_follower()
-    assert f.detect_issue(FakeTel("red")) is None
+    assert f.detect_issue(FakeTel("green")) is None
     assert f.detect_issue(FakeTel("yellow")) is None  # different colour resets
-    assert f.detect_issue(FakeTel("red")) is None     # only 1 red in a row again
+    assert f.detect_issue(FakeTel("green")) is None     # only 1 green in a row again
 
 
 def test_no_new_issue_while_halted():
@@ -204,7 +204,7 @@ def test_same_colour_refires_after_recovery():
 
     def fire_red_then_recover():
         for _ in range(3):
-            f.detect_issue(FakeTel("red"))
+            f.detect_issue(FakeTel("yellow"))
         assert f.state == ISSUE
         f.on_resume()
         f.detect_issue(FakeTel("blue"))
@@ -216,6 +216,21 @@ def test_same_colour_refires_after_recovery():
         fire_red_then_recover()
     # And confirm the third pass genuinely produced an issue each time.
     for _ in range(2):
-        assert f.detect_issue(FakeTel("red")) is None
+        assert f.detect_issue(FakeTel("yellow")) is None
+    issue = f.detect_issue(FakeTel("yellow"))
+    assert issue is not None and issue["hazard"] == "yellow_card"
+
+
+# --- critical colours halt immediately -------------------------------------
+
+def test_critical_colour_halts_on_first_read():
+    f = make_follower()
     issue = f.detect_issue(FakeTel("red"))
     assert issue is not None and issue["hazard"] == "red_card"
+    assert f.state == ISSUE
+
+
+def test_non_critical_colour_still_needs_confirm():
+    f = make_follower()
+    assert f.detect_issue(FakeTel("yellow")) is None
+    assert f.state == FOLLOWING
'''

_PATCHED_DIFF = r'''diff --git a/line_follower.py b/line_follower.py
--- a/line_follower.py
+++ b/line_follower.py
@@ -44,6 +44,11 @@ DEFAULT_CONFIG = {
     "search_step": 3.0,           # degrees added to the sweep each lost tick
     "patch_confirm_samples": 3,   # consecutive patch reads before it counts
     "reacquire_samples": 5,       # consecutive line reads to re-arm after resume
+    # Critical colours: drop to a crawl on the FIRST read (soft stop), then halt
+    # once the normal confirm count agrees (hard stop). Stops short of a hazard
+    # without letting a one-sample glare read raise a critical Case.
+    "critical_colours": ["red"],
+    "crawl_speed": 0.06,          # 0..1 speed while a critical read is unconfirmed
 }
 
 
@@ -100,6 +105,11 @@ class LineFollower:
         """
         on_line = telemetry.colour_name == self.line_colour
 
+        # Suspected critical patch: crawl straight on while detect_issue confirms
+        # it, rather than sweeping at search speed across the hazard.
+        if telemetry.colour_name in self._config["critical_colours"]:
+            return (self._config["crawl_speed"], 0.0)
+
         if on_line:
             self._search_offset = 0.0
             return (self._config["base_speed"], 0.0)
diff --git a/tests/test_line_follower.py b/tests/test_line_follower.py
--- a/tests/test_line_follower.py
+++ b/tests/test_line_follower.py
@@ -219,3 +219,29 @@ def test_same_colour_refires_after_recovery():
         assert f.detect_issue(FakeTel("red")) is None
     issue = f.detect_issue(FakeTel("red"))
     assert issue is not None and issue["hazard"] == "red_card"
+
+
+# --- critical colours: crawl on suspicion, halt on confirmation ------------
+
+def test_critical_read_drops_to_crawl_straight_on():
+    f = make_follower()
+    speed, offset = f.compute_drive(FakeTel("red"))
+    assert speed == 0.06  # DEFAULT crawl_speed (not in the test CONFIG)
+    assert offset == 0.0  # no search sweep across a hazard
+
+
+def test_critical_halt_still_needs_confirm_samples():
+    f = make_follower()
+    assert f.detect_issue(FakeTel("red")) is None
+    assert f.detect_issue(FakeTel("red")) is None
+    issue = f.detect_issue(FakeTel("red"))
+    assert issue is not None and issue["hazard"] == "red_card"
+
+
+def test_single_glare_read_crawls_then_carries_on():
+    f = make_follower()
+    f.compute_drive(FakeTel("red"))
+    assert f.detect_issue(FakeTel("red")) is None
+    speed, _ = f.compute_drive(FakeTel("blue"))
+    assert f.detect_issue(FakeTel("blue")) is None
+    assert speed == 0.3 and f.state == FOLLOWING
'''


def base_diff() -> str:
    """First pass: red halts on the FIRST colour read instead of waiting for the
    3-read confirm. Stops sooner, but a one-frame glare read now raises a
    critical Case — the flaw the track replay catches."""
    return _DRAFT_DIFF


def patch_diff() -> str:
    """After the replay fails: keep the 3-read confirm, but crawl straight on at
    the first red read so the robot is nearly stopped when the halt confirms."""
    return _PATCHED_DIFF


# --- Check verdicts: the replay fail → patch → clean pass loop ----------------
def check_fail_report() -> str:
    r = REPLAY
    return (
        ":red_circle: *Track replay — FAILED*\n"
        f"• Replayed *{r['laps']} laps* ({r['source']}) against the change. Stopping distance past "
        f"the red card's edge dropped from *{r['stop_cm_before']} cm* to *{r['stop_cm_draft']} cm*. That part works.\n"
        f"• But one-frame red reads aren't rare: the tape seam under the stand lights reads red for a "
        f"single frame *{r['glare_frames']} times* in {r['laps']} laps. With a one-read halt, every one is a "
        f"*false critical stop*: a red Case, a Slack alert and someone walking to the stand.\n"
        "> The debounce wasn't the bug. It was doing its job, just at full speed.\n"
        "Want me to patch it? I'll keep the 3-read confirm, drop to a crawl on the first red read, "
        "and drive straight on rather than sweeping across the hazard."
    )


def check_pass_report() -> str:
    r = REPLAY
    return (
        ":large_green_circle: *Track replay — clean pass*\n"
        f"• Same {r['laps']} laps: the robot stops *{r['stop_cm_after']} cm* past the edge "
        f"(was {r['stop_cm_before']} cm), with *{r['false_stops_after']}* false critical stops "
        f"(the first pass had {r['false_stops_draft']}).\n"
        f"• The {r['glare_frames']} glare frames now cause a brief crawl and the robot carries on. "
        f"All *{r['laps']}* real red cards still halted.\n"
        f"• `pytest`: *{r['tests_passed']} passed*, including 3 new tests for the crawl, the confirm and the glare case.\n"
        "0 issues. Safe for the next heat break."
    )


# --- Dashboard tab: the stop-distance numbers (Block Kit) ---------------------
def _dashboard_rows() -> list[tuple[str, str, str, str]]:
    r = REPLAY
    drop = round(100 * (r["stop_cm_before"] - r["stop_cm_after"]) / r["stop_cm_before"])
    return [
        # (label, before, after, delta)
        ("Stop distance past the red card", f"{r['stop_cm_before']} cm", f"*{r['stop_cm_after']} cm*",
         f":arrow_down: -{drop}%"),
        ("Red cards caught", f"{r['laps']}/{r['laps']}", f"*{r['laps']}/{r['laps']}*", "held"),
        ("False critical stops", "0", f"*{r['false_stops_after']}*",
         f"held (first pass: {r['false_stops_draft']})"),
        ("Tests", "47 passed", f"*{r['tests_passed']} passed*", "+3 new"),
    ]


def dashboard_blocks() -> list[dict]:
    """The Dashboard tab as a Block Kit blocks list (real array via blocks=, not a
    json.dumps'd string). mrkdwn bold is single-asterisk."""
    rows = "\n".join(
        f"• *{label}*  `{before}` → {after}   _{delta}_"
        for (label, before, after, delta) in _dashboard_rows()
    )
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "Edinburgh red card: before → after"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": rows}},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"Track replay · {REPLAY['laps']} laps · `{REPO}` · scoped to channel members"},
        ]},
    ]


# --- Recap tab: the 5-slide postmortem (canvas markdown) ----------------------
def recap_canvas() -> str:
    """5 slide-like sections built from the SAME facts as the dashboard, framed as
    a blameless postmortem. Canvas markdown: `##` headings, single-asterisk bold."""
    r = REPLAY
    return "\n\n".join([
        "## 1 · What happened",
        f"The Edinburgh robot hit a red card and halted *{r['stop_cm_before']} cm* past it. It needed 3 red "
        "readings in a row before stopping, and at racing speed that's a hand-width of travel. The Pit Crew "
        "agent diagnosed it and, by design, left the red card to people.",

        "## 2 · Who was involved",
        "The track safety lead raised it, the robotics engineer found the cause and reviewed the change, "
        "telemetry supplied the replay, and the coding agent wrote the change and the tests. Four people "
        "and an agent, one channel, one heat break.",

        "## 3 · Caught in review",
        f"The first pass halted on the first red read. The replay showed it would have raised "
        f"*{r['false_stops_draft']} false critical stops* in {r['laps']} laps: glare on the tape seam. "
        "The reviewer asked for the replay before approving, which is exactly why a reviewer is there.",

        "## 4 · What shipped",
        f"A soft stop and a hard stop: crawl on the first red read, halt once it's confirmed. Stop distance "
        f"`{r['stop_cm_before']} cm` → *{r['stop_cm_after']} cm*, false stops *{r['false_stops_after']}*, "
        f"all {r['laps']} red cards caught, *{r['tests_passed']}* tests passing. Tunable live in `params.json`.",

        "## 5 · Follow-ups",
        "Add the track replay to CI so a detection change can't merge without it, recalibrate the colour "
        "sensor under event lighting, and apply the same soft/hard stop review to the yellow and green cards.",
    ])


# --- Decision provenance: injected into the session so follow-ups recall it ---
def provenance() -> dict[str, str]:
    """decision → rationale, primed into the first agent turn so a later
    '@Claude why …?' answers from recorded reasoning."""
    return {
        "first_pass_halt_on_first_read": (
            "The first pass made red halt on the first colour read, because the complaint was stopping "
            "distance and the 3-read confirm was the obvious cause. It does stop sooner. Whether "
            "single-frame red reads happen on this track was an open question for the replay."
        ),
        "keep_the_debounce": (
            "The replay showed single-frame red reads from glare on the tape seam. The debounce exists to "
            "reject exactly those, so removing it turned glare into critical Cases. The fix keeps it."
        ),
        "crawl_then_confirm": (
            "Soft stop, then hard stop: crawl at 0.06 on the first red read, halt when the normal 3-read "
            "confirm agrees. The robot is nearly stationary by the time it's sure, so the stop is short "
            "and a glare frame only costs a brief crawl."
        ),
        "drive_straight_not_sweep": (
            "A red read isn't the line colour, so the old code started its lost-line search sweep, "
            "swinging across the hazard. The crawl drives straight on instead."
        ),
        "config_not_code": (
            "critical_colours and crawl_speed live in the line_follow config, which params.json overrides "
            "and the robot hot-reloads, so the event team can tune them without a redeploy."
        ),
    }


def render_provenance() -> str:
    lines = [
        "Decisions on this red-card fix and why (use these if asked to explain your choices). "
        "Only explain a decision once it has happened in the channel: before the track replay "
        "fails, talk about the first pass only.",
    ]
    for key, why in provenance().items():
        lines.append(f"- {key}: {why}")
    return "\n".join(lines)


# --- Thinking-pulse lines -------------------------------------------------------
_THINKING = {
    "open": "Reading the red-card thread and the debounce in line_follower.py…",
    "check": f"Replaying {REPLAY['laps']} Edinburgh practice laps against the change…",
    "patch": "Keeping the confirm, adding a crawl on the first red read, updating the tests…",
    "metrics": "Pulling stop distance and false-stop counts from the replay…",
    "recap": "Writing up the red card: what happened, who did what, what shipped…",
}


def thinking_line(action: str) -> str:
    """The Thinking-stream line for a scripted action, or a generic fallback."""
    return _THINKING.get(action, "Working on it…")


# --- Human participants: the team in the alert thread, carried into the channel -
# Fictional names; swap them for real colleagues (see docs/robot-rumble/RUNBOOK.md).
# email_stem only matters if these personas exist in your workspace (they won't by
# default); the spoofed chime-ins post either way.
PARTICIPANTS = [
    {"name": "Priya Nair", "email_stem": "priya_nair", "role": "Robotics engineer (code reviewer)"},
    {"name": "Callum Reid", "email_stem": "callum_reid", "role": "Track safety lead (approver)"},
    {"name": "Morgan Ellis", "email_stem": "morgan_ellis", "role": "Telemetry analyst"},
]


def participant_beats() -> list[dict]:
    """Scripted human chime-ins across the review loop. Every name is one of
    PARTICIPANTS; beats within a phase post in order, a short gap apart."""
    r = REPLAY
    return [
        # The backstory, playing out as the agent picks the task up.
        {"name": "Callum Reid", "phase": "arrival",
         "text": ("It halted, but it rolled a good hand-width past the card first. If that card "
                  "were a real hazard, the robot would already be on top of it.")},
        {"name": "Priya Nair", "phase": "arrival",
         "text": ("That's the debounce in `line_follower.py`. Red has to read 3 times in a row "
                  "before it counts, and at 0.3 speed that's most of the card gone. "
                  "I'll review before anything goes near the robot.")},
        {"name": "Priya Nair", "phase": "on_artifacts",
         "text": ("Halting on a single red read? Under the stand lights that tape seam goes pinkish "
                  "for a frame. Not approving it blind. Replay yesterday's laps first.")},
        {"name": "Morgan Ellis", "phase": "on_artifacts",
         "text": f"Replay's loaded: {r['laps']} Edinburgh laps from yesterday. Say the word."},
        {"name": "Callum Reid", "phase": "on_check_fail",
         "text": (f"So we'd swap a late stop for {r['false_stops_draft']} false red alerts. Each one opens a "
                  "critical Case and pulls someone to the stand. Not shipping that.")},
        {"name": "Priya Nair", "phase": "on_check_fail",
         "text": "Keep the confirm. Slow it right down on the first red read and only halt once it's sure?"},
        {"name": "Priya Nair", "phase": "on_patch",
         "text": (":white_check_mark: Approved. Crawls straight on, keeps the confirm, and the tests "
                  "cover the glare case.")},
        {"name": "Callum Reid", "phase": "on_patch",
         "text": ("Approved for the next heat break. Maker, checker and sign-off, all in this channel. "
                  "Ship it.")},
        {"name": "Priya Nair", "phase": "on_check_pass",
         "text": "Still green. Good."},
        {"name": "Morgan Ellis", "phase": "on_recap",
         "text": "I'll pin the replay so we rerun it after every detection change."},
    ]
