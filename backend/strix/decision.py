"""
strix/decision.py — Decision Engine
=====================================
Takes the final risk score and decides what to do.

  0.00 – 0.34  →  ALLOW      (green)  genuine user
  0.35 – 0.59  →  CAPTCHA    (yellow) suspicious, verify
  0.60 – 1.00  →  BLOCK      (red)    definite bot/attack

Thresholds tightened from original (0.40/0.70) to (0.35/0.60)
so smart bots (score ~0.45–0.65) and stealth bots (score ~0.38–0.55)
no longer slip through as ALLOW.

Also stores the decision in MongoDB for dashboard display.
"""

from datetime import datetime
from pymongo import MongoClient

client    = MongoClient("mongodb://localhost:27017/")
db        = client["strixfintech"]
decisions = db["strix_decisions"]


THRESHOLDS = {
    "allow":   (0.00, 0.20),   # increased from 0.10 (legitimate users can pass up to 20%)
    "captcha": (0.21, 0.59),   # adjusted to 0.21-0.59
    "block":   (0.60, 1.00),   # kept at 0.60
}


def make_decision(score_result: dict, user_id: str) -> dict:
    """
    Input:  full score result from calculate_risk_score()
    Output: decision dict with action, reason, and metadata
    """
    score = score_result["final_score"]

    # ── Determine action ──────────────────────────────────────────────────────
    if score <= THRESHOLDS["allow"][1]:
        action    = "allow"
        color     = "green"
        message   = "Request allowed — user appears genuine"
        http_code = 200

    elif score <= THRESHOLDS["captcha"][1]:
        action    = "captcha"
        color     = "yellow"
        message   = "Suspicious activity detected — CAPTCHA required"
        http_code = 200   # frontend handles CAPTCHA display

    else:
        action    = "block"
        color     = "red"
        message   = "Request blocked — automated attack detected"
        http_code = 403

    # ── Build decision record ─────────────────────────────────────────────────
    fp = score_result.get("fingerprint", {})

    record = {
        "timestamp":   datetime.utcnow().isoformat() + 'Z',
        "user_id":     user_id,
        "ip":          score_result.get("ip", "unknown"),
        "final_score": score,
        "action":      action,
        "color":       color,
        "attack_type": fp.get("attack_type", "unknown"),
        "fp_id":       fp.get("fp_id", ""),
        "is_known_fp": fp.get("is_known", False),
        "layer_scores": {
            k: v["score"] for k, v in score_result.get("layers", {}).items()
        },
        "signals":     score_result.get("all_signals", []),
    }

    # ── Save to MongoDB ───────────────────────────────────────────────────────
    decisions.insert_one(record)

    return {
        "action":      action,
        "color":       color,
        "score":       score,
        "message":     message,
        "http_code":   http_code,
        "attack_type": fp.get("attack_type", "unknown"),
        "fp_id":       fp.get("fp_id", ""),
        "is_known_fp": fp.get("is_known", False),
        "signals":     score_result.get("all_signals", []),
        "layer_scores": record["layer_scores"],
    }


def get_recent_decisions(limit: int = 100) -> list:
    """Fetch recent decisions for the dashboard."""
    return list(decisions.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))


def get_dashboard_stats() -> dict:
    """Aggregate stats for dashboard summary cards."""
    total   = decisions.count_documents({})
    blocked = decisions.count_documents({"action": "block"})
    captcha = decisions.count_documents({"action": "captcha"})
    allowed = decisions.count_documents({"action": "allow"})

    # Count unique suspicious IPs
    suspicious_ips = len(decisions.distinct(
        "ip", {"action": {"$in": ["block", "captcha"]}}
    ))

    # Bot traffic percentage
    bot_pct = round((blocked + captcha) / total * 100, 1) if total > 0 else 0

    # Active threats (blocked in last 5 minutes)
    from datetime import timedelta
    five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    active_threats = decisions.count_documents({
        "action": "block",
        "timestamp": {"$gte": five_min_ago}
    })

    return {
        "total":           total,
        "blocked":         blocked,
        "captcha":         captcha,
        "allowed":         allowed,
        "suspicious_ips":  suspicious_ips,
        "bot_traffic_pct": bot_pct,
        "active_threats":  active_threats,
    }