from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["strixfintech"]
users_col = db["users"]
login_events_col = db["login_events"]

# ─────────────────────────────────────────────
# HELPER: log every login attempt
# ─────────────────────────────────────────────
def log_event(user_id, ip, success, reason=""):
    event = {
        "user_id": user_id,
        "ip": ip,
        "timestamp": datetime.utcnow().isoformat(),
        "success": success,
        "reason": reason,
        "device": request.headers.get("User-Agent", "unknown")[:80],
    }
    login_events_col.insert_one(event)
    print(f"[LOG] {ip} → {user_id} | success={success} | {reason}")

# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    name     = data.get("name", "")

    if not email or not password or not name:
        return jsonify({"error": "All fields required"}), 400

    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_col.insert_one({
        "email": email,
        "name": name,
        "password": hashed,
        "balance": 50000.00,
        "created_at": datetime.utcnow().isoformat()
    })
    return jsonify({"message": "Account created successfully"}), 201

# ─────────────────────────────────────────────
# LOGIN  ← This is what the bot will hammer
# ─────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    data     = request.json
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    ip       = request.headers.get("X-Forwarded-For", request.remote_addr)

    user = users_col.find_one({"email": email})

    if not user:
        log_event(email, ip, False, "user_not_found")
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode(), user["password"]):
        log_event(email, ip, False, "wrong_password")
        return jsonify({"error": "Invalid credentials"}), 401

    log_event(email, ip, True, "success")
    return jsonify({
        "message": "Login successful",
        "user": {
            "name": user["name"],
            "email": user["email"],
            "balance": user["balance"]
        }
    }), 200

# ─────────────────────────────────────────────
# GET RECENT LOGIN EVENTS (for dashboard)
# ─────────────────────────────────────────────
@app.route("/api/events", methods=["GET"])
def get_events():
    events = list(login_events_col.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))
    return jsonify(events), 200

# ─────────────────────────────────────────────
# STATS (for dashboard summary cards)
# ─────────────────────────────────────────────
@app.route("/api/stats", methods=["GET"])
def get_stats():
    total      = login_events_col.count_documents({})
    failed     = login_events_col.count_documents({"success": False})
    success    = login_events_col.count_documents({"success": True})
    unique_ips = len(login_events_col.distinct("ip"))

    return jsonify({
        "total_attempts": total,
        "failed_attempts": failed,
        "success_attempts": success,
        "unique_ips": unique_ips
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)