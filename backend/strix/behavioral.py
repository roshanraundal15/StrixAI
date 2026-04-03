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
    max_points += 4   # increased from 3 → stronger keystroke detection

    if len(keystroke_intervals) > 3:
        avg      = sum(keystroke_intervals) / len(keystroke_intervals)
        diffs    = [abs(k - avg) for k in keystroke_intervals]
        variance = sum(diffs) / len(diffs)
        std_dev  = (sum(d**2 for d in diffs) / len(diffs)) ** 0.5

        # Check for consistent patterns (bots try to look human but are too uniform)
        # Exclude the large pause(s) to analyze the rapid keystrokes
        quick_intervals = [k for k in keystroke_intervals if k < 300]
        if len(quick_intervals) > 2:
            quick_avg = sum(quick_intervals) / len(quick_intervals)
            quick_diffs = [abs(k - quick_avg) for k in quick_intervals]
            quick_variance = sum(quick_diffs) / len(quick_diffs)
        else:
            quick_variance = variance

        # Human keystroke variance: typically 40-100ms
        # Stealth bot: tries for 30-50ms with controlled pauses
        if variance < 10:
            # Perfectly spaced keystrokes — definite bot
            risk_points += 4
            signals.append("⚠ Perfectly uniform keystroke timing (bot pattern)")
        elif variance < 15:
            # Suspiciously tight distribution — stealth bot signature
            risk_points += 3
            signals.append("⚠ Unusually uniform keystroke timing (stealth bot signature)")
        elif variance < 25:
            # Still too uniform for realistic human
            risk_points += 2
            signals.append("⚠ Keystroke variance suspiciously low")
        elif variance < 35 and std_dev < 25:
            # Even with pauses, if std_dev is still low = controlled bot
            risk_points += 1
            signals.append("! Keystroke pattern shows artificial regularity")
        elif quick_variance < 20 and len(quick_intervals) >= 3:
            # Fast keystrokes are too uniform (even when ignoring pauses)
            risk_points += 2
            signals.append("⚠ Rapid keystrokes show unnatural consistency")
            
    elif len(keystroke_intervals) == 0 and time_to_submit and time_to_submit < 3000:
        # Fast submit with ZERO keystrokes = credentials were pasted (bot signature)
        risk_points += 3
        signals.append("⚠ No keystrokes detected — credentials likely pasted")
    elif len(keystroke_intervals) == 0:
        # REMOVED: Don't penalize for zero keystroke data if submit time is reasonable
        # Some apps may not capture keystroke intervals properly
        signals.append("ℹ Keystroke data unavailable (app limitation)")

    # ── 3. Mouse movement ────────────────────────────────────────────────────
    mouse_moves = data.get("mouse_move_count", 0)
    max_points += 3   # increased from 2 → minimal mouse is a stronger signal

    if mouse_moves == 0:
        risk_points += 3
        signals.append("⚠ Zero mouse movement detected")
    elif mouse_moves < 5:
        # Smart bot sends 2–8 moves — still too low for a real human
        risk_points += 2
        signals.append(f"⚠ Very minimal mouse movement ({mouse_moves} events)")
    elif mouse_moves < 10:
        risk_points += 1
        signals.append(f"! Low mouse movement ({mouse_moves} events)")

    # ── 4. Password paste detection ─────────────────────────────────────────
    password_pasted = data.get("password_pasted", False)
    max_points += 2   # increased from 1 → pasting is a strong bot signal

    if password_pasted:
        risk_points += 2
        signals.append("⚠ Password was pasted (strong bot indicator)")

    # ── 5. Field focus pattern ───────────────────────────────────────────────
    # Did user tab/click between fields naturally?
    field_focus_count = data.get("field_focus_count", 0)
    max_points += 1

    if field_focus_count == 0:
        risk_points += 1
        signals.append("⚠ No field focus events — form filled programmatically")
    elif field_focus_count == 1:
        # Smart bot sends exactly 1 focus — humans typically hit 2+
        risk_points += 0   # no extra penalty but noted in signals
        signals.append("! Only 1 field focus event")

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