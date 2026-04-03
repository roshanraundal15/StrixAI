"""
strix/honeypot.py — Layer 4: Honeypot / Bot Trap
=================================================
Invisible traps in the login form that only bots trigger.

Trap 1 — Hidden field
  A CSS-hidden input field named "phone" is added to the
  login form. Real users never see it or fill it.
  Bots that auto-fill all form fields will fill it.
  → If filled: instant HIGH risk

Trap 2 — Timing trap
  The form has a hidden timestamp injected when the page loads.
  If the form is submitted before 1.5 seconds have passed,
  the page was never actually rendered in a browser.
  → If too fast: HIGH risk

Trap 3 — JavaScript disabled
  Real browsers execute JS to set a hidden "js_enabled" field.
  If it's missing, the request likely came from a script.
  → If missing: MEDIUM risk
"""


def check_honeypot(data: dict) -> dict:
    """
    Input:  request data dict (form fields + metadata)
    Output: { triggered: bool, score: 0.0-1.0, signals: [...] }

    Score of 1.0 means honeypot was triggered = instant block territory
    """
    signals     = []
    risk_points = 0
    max_points  = 5

    # ── Trap 1: Hidden phone field filled ────────────────────────────────────
    honeypot_field = data.get("phone", "")     # this field is hidden in CSS
    if honeypot_field and str(honeypot_field).strip() != "":
        risk_points += 3
        signals.append("🚨 HONEYPOT TRIGGERED: Hidden field was filled — definite bot")

    # ── Trap 2: Form submitted impossibly fast ────────────────────────────────
    time_to_submit = data.get("time_to_submit", None)
    if time_to_submit is not None and time_to_submit < 800:
        risk_points += 1
        signals.append(f"⚠ Form submitted in {time_to_submit}ms — faster than humanly possible")

    # ── Trap 3: JavaScript disabled / not executed ────────────────────────────
    js_enabled = data.get("js_enabled", None)
    if js_enabled is None:
        risk_points += 1
        signals.append("⚠ JS fingerprint missing — request may not be from a real browser")
    elif js_enabled is False:
        risk_points += 1
        signals.append("⚠ JavaScript was disabled in the client")

    triggered = risk_points >= 3   # honeypot field alone = triggered
    score     = round(min(risk_points / max_points, 1.0), 3)

    if not signals:
        signals.append("✓ No honeypot traps triggered")

    return {
        "triggered": triggered,
        "score":     score,
        "signals":   signals,
    }