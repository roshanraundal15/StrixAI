"""
strix/behavioral.py — Layer 1: Behavioral Biometrics
=====================================================
Analyzes typing rhythm, mouse movement, time-to-submit
to distinguish humans from bots.

A real human:
  - Takes 5–60 seconds to fill the form
  - Has irregular keystroke intervals (not perfectly timed)
  - Moves the mouse before clicking submit
  - Types the password (doesn't paste it)

A bot:
  - Submits in under 1 second
  - Has perfectly uniform keystroke timing
  - No mouse movement
  - Pastes credentials instantly
"""

def analyze_behavior(data: dict) -> dict:
    """
    Input:  behavioral data dict from frontend
    Output: { score: 0.0-1.0, signals: [...], details: {...} }
    
    Score closer to 1.0 = more bot-like
    Score closer to 0.0 = more human-like
    """
    signals     = []
    risk_points = 0
    max_points  = 0

    # ── 1. Time to submit ────────────────────────────────────────────────────
    # How many milliseconds from page load to form submit
    time_to_submit = data.get("time_to_submit", None)   # ms
    max_points += 3

    if time_to_submit is not None:
        if time_to_submit < 1000:
            # Under 1 second — almost certainly a bot
            risk_points += 3
            signals.append("⚠ Submitted in under 1 second")
        elif time_to_submit < 3000:
            # Under 3 seconds — very suspicious
            risk_points += 2
            signals.append("⚠ Extremely fast form submission")
        elif time_to_submit < 5000:
            risk_points += 1
            signals.append("! Fast form submission")
        # 5–60 seconds = normal human range, no points
    else:
        # No timing data sent = likely a direct API call (bot)
        risk_points += 3
        signals.append("⚠ No timing data — direct API call suspected")

    # ── 2. Keystroke uniformity ──────────────────────────────────────────────
    # List of time gaps between keypresses (ms)
    keystroke_intervals = data.get("keystroke_intervals", [])
    max_points += 2

    if len(keystroke_intervals) > 3:
        avg   = sum(keystroke_intervals) / len(keystroke_intervals)
        diffs = [abs(k - avg) for k in keystroke_intervals]
        variance = sum(diffs) / len(diffs)

        if variance < 10:
            # All keystrokes perfectly spaced — bot
            risk_points += 2
            signals.append("⚠ Perfectly uniform keystroke timing (bot pattern)")
        elif variance < 30:
            risk_points += 1
            signals.append("! Suspiciously uniform keystroke timing")
    elif len(keystroke_intervals) == 0 and time_to_submit and time_to_submit < 3000:
        # Fast submit with zero keystrokes = credentials were pasted
        risk_points += 2
        signals.append("⚠ No keystrokes detected — credentials likely pasted")

    # ── 3. Mouse movement ────────────────────────────────────────────────────
    mouse_moves = data.get("mouse_move_count", 0)
    max_points += 2

    if mouse_moves == 0:
        risk_points += 2
        signals.append("⚠ Zero mouse movement detected")
    elif mouse_moves < 3:
        risk_points += 1
        signals.append("! Minimal mouse movement")

    # ── 4. Password paste detection ─────────────────────────────────────────
    password_pasted = data.get("password_pasted", False)
    max_points += 1

    if password_pasted:
        risk_points += 1
        signals.append("! Password was pasted (not typed)")

    # ── 5. Field focus pattern ───────────────────────────────────────────────
    # Did user tab/click between fields naturally?
    field_focus_count = data.get("field_focus_count", 0)
    max_points += 1

    if field_focus_count == 0:
        risk_points += 1
        signals.append("⚠ No field focus events — form filled programmatically")

    # ── Calculate final score ────────────────────────────────────────────────
    score = round(risk_points / max_points, 3) if max_points > 0 else 0.5

    return {
        "score":   score,
        "signals": signals,
        "details": {
            "time_to_submit":      time_to_submit,
            "keystroke_intervals": keystroke_intervals,
            "mouse_moves":         mouse_moves,
            "password_pasted":     password_pasted,
            "field_focus_count":   field_focus_count,
        }
    }