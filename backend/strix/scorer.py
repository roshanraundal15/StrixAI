"""
strix/scorer.py — Risk Score Combiner
======================================
Combines outputs from all 4 detection layers
into a single Final Confidence Score (0.0 – 1.0)

Layer weights:
  Honeypot   → 35%  (highest — if triggered, almost certain bot)
  Behavioral → 30%  (typing/mouse patterns)
  Session    → 25%  (ML + rule-based pattern)
  Network    → 10%  (IP reputation)

If honeypot is triggered → score is immediately floored at 0.85
"""

from .behavioral import analyze_behavior
from .network    import check_ip
from .session    import analyze_session
from .honeypot   import check_honeypot
from .fingerprint import generate_fingerprint


WEIGHTS = {
    "honeypot":   0.35,
    "behavioral": 0.30,
    "session":    0.25,
    "network":    0.10,
}


def calculate_risk_score(login_data: dict, ip: str) -> dict:
    """
    Main entry point for Strix AI.

    Input:
        login_data — everything from the frontend login request
        ip         — the client IP address

    Output:
        Full analysis result with final score, all layer scores,
        signals, fingerprint, and decision recommendation
    """

    # ── Run all 4 layers ──────────────────────────────────────────────────────
    honeypot_result   = check_honeypot(login_data)
    behavioral_result = analyze_behavior(login_data)
    session_result    = analyze_session(ip)
    network_result    = check_ip(ip)

    # ── Generate attack fingerprint ───────────────────────────────────────────
    fp = generate_fingerprint(
        behavioral = behavioral_result,
        network    = network_result,
        session    = session_result,
        ip         = ip
    )

    # ── Weighted score combination ────────────────────────────────────────────
    raw_score = (
        honeypot_result["score"]   * WEIGHTS["honeypot"]   +
        behavioral_result["score"] * WEIGHTS["behavioral"] +
        session_result["score"]    * WEIGHTS["session"]    +
        network_result["score"]    * WEIGHTS["network"]
    )

    # If honeypot was triggered, enforce minimum score of 0.85
    if honeypot_result["triggered"]:
        raw_score = max(raw_score, 0.85)

    # If known attack fingerprint seen 3+ times, boost score
    if fp["is_known"] and fp["seen_count"] >= 3:
        raw_score = min(raw_score + 0.15, 1.0)

    final_score = round(raw_score, 3)

    # ── Collect all signals ───────────────────────────────────────────────────
    all_signals = (
        honeypot_result["signals"] +
        behavioral_result["signals"] +
        session_result["signals"] +
        network_result["signals"]
    )

    return {
        "final_score": final_score,
        "layers": {
            "honeypot":   {"score": honeypot_result["score"],   "signals": honeypot_result["signals"]},
            "behavioral": {"score": behavioral_result["score"], "signals": behavioral_result["signals"]},
            "session":    {"score": session_result["score"],    "signals": session_result["signals"]},
            "network":    {"score": network_result["score"],    "signals": network_result["signals"]},
        },
        "fingerprint": fp,
        "all_signals": all_signals,
        "ip": ip,
    }