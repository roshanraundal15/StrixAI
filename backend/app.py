from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import bcrypt

from strix.scorer   import calculate_risk_score
from strix.decision import make_decision, get_recent_decisions, get_dashboard_stats
from strix.fingerprint import get_all_fingerprints

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db     = client["strixfintech"]
users_col        = db["users"]
login_events_col = db["login_events"]


def log_event(user_id, ip, success, reason="", strix_decision=None):
    event = {
        "user_id":   user_id,
        "ip":        ip,
        "timestamp": datetime.utcnow().isoformat(),
        "success":   success,
        "reason":    reason,
        "device":    request.headers.get("User-Agent", "unknown")[:80],
    }
    if strix_decision:
        event["strix_action"] = strix_decision.get("action")
        event["strix_score"]  = strix_decision.get("score")
    login_events_col.insert_one(event)
    print(f"[LOG] {ip} -> {user_id} | success={success} | {reason}")


@app.route("/api/register", methods=["POST"])
def register():
    data     = request.json
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    name     = data.get("name", "")
    if not email or not password or not name:
        return jsonify({"error": "All fields required"}), 400
    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_col.insert_one({
        "email": email, "name": name, "password": hashed,
        "balance": 50000.00, "created_at": datetime.utcnow().isoformat()
    })
    return jsonify({"message": "Account created successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data     = request.json or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    ip       = request.headers.get("X-Forwarded-For", request.remote_addr)

    score_result = calculate_risk_score(data, ip)
    decision     = make_decision(score_result, email)
    print(f"[Strix] {ip} | score={decision['score']} | action={decision['action']} | type={decision['attack_type']}")

    if decision["action"] == "block":
        log_event(email, ip, False, "strix_blocked", decision)
        return jsonify({"error": "Access denied", "strix": decision, "blocked": True}), 403

    user = users_col.find_one({"email": email})
    if not user:
        log_event(email, ip, False, "user_not_found", decision)
        return jsonify({"error": "Invalid credentials", "strix": decision}), 401
    if not bcrypt.checkpw(password.encode(), user["password"]):
        log_event(email, ip, False, "wrong_password", decision)
        return jsonify({"error": "Invalid credentials", "strix": decision}), 401

    log_event(email, ip, True, "success", decision)
    response = {
        "message": "Login successful",
        "user": {"name": user["name"], "email": user["email"], "balance": user["balance"]},
        "strix": decision
    }
    if decision["action"] == "captcha":
        response["captcha_required"] = True
    return jsonify(response), 200


@app.route("/api/strix/stats",        methods=["GET"])
def strix_stats():      return jsonify(get_dashboard_stats()), 200

@app.route("/api/strix/decisions",    methods=["GET"])
def strix_decisions():  return jsonify(get_recent_decisions()), 200

@app.route("/api/strix/fingerprints", methods=["GET"])
def strix_fingerprints(): return jsonify(get_all_fingerprints()), 200

@app.route("/api/events", methods=["GET"])
def get_events():
    events = list(login_events_col.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))
    return jsonify(events), 200

@app.route("/api/stats", methods=["GET"])
def get_stats():
    total     = login_events_col.count_documents({})
    failed    = login_events_col.count_documents({"success": False})
    success   = login_events_col.count_documents({"success": True})
    unique_ips= len(login_events_col.distinct("ip"))
    return jsonify({"total_attempts": total, "failed_attempts": failed,
                    "success_attempts": success, "unique_ips": unique_ips}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)