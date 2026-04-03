"""
strix/session.py — Layer 3: Session Pattern Analysis
=====================================================
Uses Isolation Forest (unsupervised ML) to detect
anomalous login patterns from MongoDB event history.

Features analyzed per IP:
  - login_attempt_rate     (attempts per minute)
  - failed_login_ratio     (failed / total)
  - unique_users_per_ip    (how many accounts targeted)
  - avg_time_between_reqs  (seconds between requests)
  - session_count          (total sessions from this IP)

Low-and-slow attack detection:
  - Tracks attempts over a longer window (24 hours)
  - Flags IPs that slowly accumulate failed attempts
    across many accounts even at low rate
"""

import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from pymongo import MongoClient

# ── MongoDB connection ────────────────────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017/")
db     = client["strixfintech"]
events = db["login_events"]

# ── Global model (trained on first use, retrained periodically) ──────────────
_model      = None
_last_train = None
RETRAIN_INTERVAL_MINS = 10   # retrain every 10 minutes with new data


def _extract_features(ip: str, window_minutes: int = 5) -> dict:
    """Extract behavioral features for a given IP over the last N minutes."""
    now       = datetime.utcnow()
    since     = (now - timedelta(minutes=window_minutes)).isoformat()
    since_24h = (now - timedelta(hours=24)).isoformat()

    # Recent window (last N minutes)
    recent = list(events.find({"ip": ip, "timestamp": {"$gte": since}}))

    # 24-hour window for low-and-slow detection
    day_events = list(events.find({"ip": ip, "timestamp": {"$gte": since_24h}}))

    total   = len(recent)
    failed  = sum(1 for e in recent if not e.get("success", True))
    users   = len(set(e.get("user_id", "") for e in recent))

    # Time gaps between requests
    timestamps = sorted([e["timestamp"] for e in recent])
    if len(timestamps) > 1:
        gaps = []
        for i in range(1, len(timestamps)):
            try:
                t1 = datetime.fromisoformat(timestamps[i-1])
                t2 = datetime.fromisoformat(timestamps[i])
                gaps.append((t2 - t1).total_seconds())
            except Exception:
                pass
        avg_gap = sum(gaps) / len(gaps) if gaps else 999
    else:
        avg_gap = 999

    attempt_rate = total / window_minutes if window_minutes > 0 else 0
    fail_ratio   = failed / total if total > 0 else 0

    # Low-and-slow: many unique users targeted over 24h at low rate
    day_users   = len(set(e.get("user_id", "") for e in day_events))
    day_total   = len(day_events)
    day_failed  = sum(1 for e in day_events if not e.get("success", True))
    day_fail_ratio = day_failed / day_total if day_total > 0 else 0

    return {
        "attempt_rate":       attempt_rate,
        "fail_ratio":         fail_ratio,
        "unique_users":       users,
        "avg_gap_secs":       avg_gap,
        "session_count":      total,
        "day_unique_users":   day_users,
        "day_total":          day_total,
        "day_fail_ratio":     day_fail_ratio,
    }


def _get_training_data():
    """
    Pull feature vectors for all IPs seen in last hour.
    Used to train the Isolation Forest.
    """
    since = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    ips   = events.distinct("ip", {"timestamp": {"$gte": since}})

    vectors = []
    for ip in ips:
        f = _extract_features(ip)
        vectors.append([
            f["attempt_rate"],
            f["fail_ratio"],
            f["unique_users"],
            min(f["avg_gap_secs"], 300),   # cap at 300s
            f["session_count"],
        ])

    return vectors if len(vectors) >= 5 else None


def _train_model():
    """Train or retrain the Isolation Forest model."""
    global _model, _last_train

    data = _get_training_data()
    if data is None:
        return False   # not enough data yet

    X = np.array(data)
    _model = IsolationForest(
        n_estimators=100,
        contamination=0.15,   # expect ~15% anomalous traffic
        random_state=42
    )
    _model.fit(X)
    _last_train = datetime.utcnow()
    print(f"[Strix] Isolation Forest trained on {len(data)} IP samples")
    return True


def _should_retrain() -> bool:
    if _last_train is None:
        return True
    elapsed = (datetime.utcnow() - _last_train).total_seconds() / 60
    return elapsed >= RETRAIN_INTERVAL_MINS


def analyze_session(ip: str) -> dict:
    """
    Input:  IP address
    Output: { score: 0.0-1.0, signals: [...], details: {...} }
    """
    global _model

    signals = []
    features = _extract_features(ip)

    # ── Rule-based checks (always run, no ML needed) ─────────────────────────
    rule_risk   = 0
    rule_max    = 6

    # High attempt rate
    if features["attempt_rate"] > 10:
        rule_risk += 2
        signals.append(f"⚠ Very high attempt rate: {features['attempt_rate']:.1f}/min")
    elif features["attempt_rate"] > 3:
        rule_risk += 1
        signals.append(f"! Elevated attempt rate: {features['attempt_rate']:.1f}/min")

    # High failure ratio
    if features["fail_ratio"] > 0.9:
        rule_risk += 2
        signals.append(f"⚠ Very high failure ratio: {features['fail_ratio']*100:.0f}%")
    elif features["fail_ratio"] > 0.6:
        rule_risk += 1
        signals.append(f"! High failure ratio: {features['fail_ratio']*100:.0f}%")

    # Many unique users targeted (credential stuffing)
    if features["unique_users"] > 10:
        rule_risk += 2
        signals.append(f"⚠ Targeting {features['unique_users']} different accounts — credential stuffing")
    elif features["unique_users"] > 3:
        rule_risk += 1
        signals.append(f"! Multiple accounts targeted: {features['unique_users']}")

    # ── Low-and-slow detection ────────────────────────────────────────────────
    low_slow_risk = 0
    if features["day_unique_users"] > 20 and features["attempt_rate"] < 2:
        low_slow_risk = 0.6
        signals.append(f"⚠ LOW-AND-SLOW: {features['day_unique_users']} accounts targeted over 24h at low rate")
    elif features["day_unique_users"] > 10 and features["day_fail_ratio"] > 0.7:
        low_slow_risk = 0.4
        signals.append(f"! Slow distributed attack pattern detected over 24h")

    rule_score = rule_risk / rule_max

    # ── ML-based anomaly detection ────────────────────────────────────────────
    ml_score = 0.0

    if _should_retrain():
        _train_model()

    if _model is not None:
        try:
            vector = np.array([[
                features["attempt_rate"],
                features["fail_ratio"],
                features["unique_users"],
                min(features["avg_gap_secs"], 300),
                features["session_count"],
            ]])
            prediction = _model.predict(vector)[0]    # -1 = anomaly, 1 = normal
            raw_score  = _model.decision_function(vector)[0]

            if prediction == -1:
                # Anomaly detected — normalize the score
                ml_score = min(abs(raw_score) * 0.5 + 0.4, 1.0)
                signals.append(f"⚠ ML model flagged as anomaly (score: {ml_score:.2f})")
            else:
                ml_score = max(0.0, 0.3 - raw_score * 0.1)
                signals.append(f"✓ ML model: normal pattern (score: {ml_score:.2f})")
        except Exception as e:
            signals.append(f"! ML scoring error: {str(e)}")
            ml_score = rule_score   # fallback to rule score

    else:
        # Not enough data to train yet — use rule score only
        ml_score = rule_score
        if not signals:
            signals.append("ℹ Insufficient data for ML — using rule-based scoring")

    # ── Combine rule + ML + low-and-slow ─────────────────────────────────────
    final_score = round(
        (rule_score * 0.4) + (ml_score * 0.4) + (low_slow_risk * 0.2),
        3
    )

    if not signals:
        signals.append("✓ Session pattern looks normal")

    return {
        "score":   final_score,
        "signals": signals,
        "details": features
    }