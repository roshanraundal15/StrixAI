"""
strix/fingerprint.py — Attack Fingerprinting
=============================================
Generates a unique fingerprint for each attack pattern.
Stores it in MongoDB so future similar attacks are
recognized instantly — even from different IPs/devices.

A fingerprint is based on:
  - Behavioral signature (typing speed bucket, mouse pattern)
  - Network signature (ASN, hosting flag, proxy flag)
  - Session signature (attempt rate bucket, fail ratio bucket, unique users)
  - Attack type classification
"""

import hashlib
import json
from datetime import datetime
from pymongo import MongoClient

client     = MongoClient("mongodb://localhost:27017/")
db         = client["strixfintech"]
fp_col     = db["attack_fingerprints"]


def _bucket(value, thresholds: list, labels: list) -> str:
    """Map a numeric value to a named bucket."""
    for thresh, label in zip(thresholds, labels):
        if value <= thresh:
            return label
    return labels[-1]


def generate_fingerprint(
    behavioral: dict,
    network: dict,
    session: dict,
    ip: str
) -> dict:
    """
    Build a fingerprint dict and a short hash ID from detection layer outputs.
    """
    b = behavioral.get("details", {})
    n = network.get("details", {})
    s = session.get("details", {})

    # ── Normalize values into buckets ─────────────────────────────────────────
    speed_bucket = _bucket(
        b.get("time_to_submit", 9999),
        [800, 2000, 5000, 15000],
        ["instant", "very_fast", "fast", "normal", "slow"]
    )

    rate_bucket = _bucket(
        s.get("attempt_rate", 0),
        [0.5, 2, 5, 15],
        ["minimal", "low", "medium", "high", "very_high"]
    )

    fail_bucket = _bucket(
        s.get("fail_ratio", 0),
        [0.2, 0.5, 0.8, 0.95],
        ["low", "medium", "high", "very_high", "total"]
    )

    user_bucket = _bucket(
        s.get("unique_users", 1),
        [1, 3, 10, 30],
        ["single", "few", "many", "mass", "bulk"]
    )

    # ── Classify attack type ──────────────────────────────────────────────────
    attack_type = "unknown"
    if s.get("unique_users", 1) > 5 and s.get("fail_ratio", 0) > 0.7:
        attack_type = "credential_stuffing"
    elif s.get("attempt_rate", 0) > 10:
        attack_type = "brute_force"
    elif s.get("day_unique_users", 0) > 15 and s.get("attempt_rate", 0) < 2:
        attack_type = "low_and_slow"
    elif n.get("proxy", False) or n.get("hosting", False):
        attack_type = "proxy_attack"
    elif behavioral.get("score", 0) > 0.7:
        attack_type = "automated_bot"

    # ── Build fingerprint signature ───────────────────────────────────────────
    signature = {
        "speed":       speed_bucket,
        "rate":        rate_bucket,
        "fail_ratio":  fail_bucket,
        "user_spread": user_bucket,
        "is_proxy":    bool(n.get("proxy", False)),
        "is_hosting":  bool(n.get("hosting", False)),
        "attack_type": attack_type,
        "no_mouse":    b.get("mouse_moves", 1) == 0,
        "pasted":      bool(b.get("password_pasted", False)),
    }

    # ── Generate hash ID from signature ──────────────────────────────────────
    sig_str    = json.dumps(signature, sort_keys=True)
    fp_hash    = hashlib.sha256(sig_str.encode()).hexdigest()[:16].upper()
    fp_id      = f"FP-{fp_hash}"

    # ── Check if this fingerprint was seen before ─────────────────────────────
    existing = fp_col.find_one({"fp_id": fp_id})
    is_known = existing is not None
    seen_count = existing.get("seen_count", 0) + 1 if existing else 1

    # ── Store / update fingerprint in DB ─────────────────────────────────────
    fp_col.update_one(
        {"fp_id": fp_id},
        {"$set": {
            "fp_id":       fp_id,
            "signature":   signature,
            "attack_type": attack_type,
            "last_seen":   datetime.utcnow().isoformat(),
            "last_ip":     ip,
        }, "$inc": {"seen_count": 1}},
        upsert=True
    )

    return {
        "fp_id":       fp_id,
        "attack_type": attack_type,
        "signature":   signature,
        "is_known":    is_known,
        "seen_count":  seen_count,
    }


def get_all_fingerprints(limit: int = 50) -> list:
    """Fetch recent fingerprints for the dashboard."""
    fps = list(fp_col.find({}, {"_id": 0}).sort("last_seen", -1).limit(limit))
    return fps