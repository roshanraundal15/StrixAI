"""
app.py — NovaPay Backend + Strix AI
=====================================
All routes in one file. Replace your existing app.py with this entirely.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import bcrypt
import uuid

from strix.scorer   import calculate_risk_score
from strix.decision import make_decision

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db     = client["strixfintech"]

# ── Collections ───────────────────────────────────────────────────────────────
col_users       = db["users"]
col_events      = db["login_events"]
col_decisions   = db["strix_decisions"]
col_txns        = db["transactions"]
col_fingerprints = db["attack_fingerprints"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else request.remote_addr


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/register", methods=["POST"])
def register():
    data  = request.json
    email = data.get("email", "").lower().strip()
    pwd   = data.get("password", "")
    name  = data.get("name", "")

    if not email or not pwd or not name:
        return jsonify({"error": "All fields required"}), 400
    if col_users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
    user = {
        "name":       name,
        "email":      email,
        "password":   hashed,
        "balance":    1000.00,
        "account_no": str(uuid.uuid4())[:8].upper(),
        "created_at": datetime.utcnow().isoformat(),
    }
    result = col_users.insert_one(user)

    return jsonify({
        "message": "Account created",
        "user": {
            "id":         str(result.inserted_id),
            "name":       name,
            "email":      email,
            "balance":    user["balance"],
            "account_no": user["account_no"],
        }
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data  = request.json
    email = data.get("email", "").lower().strip()
    pwd   = data.get("password", "")
    ip    = get_client_ip()

    # ── Strix AI Analysis ─────────────────────────────────────────────────────
    score_result = calculate_risk_score(data, ip)
    decision     = make_decision(score_result, email)

    # Log event to login_events
    event = {
        "timestamp":   datetime.utcnow().isoformat(),
        "ip":          ip,
        "email":       email,
        "action":      decision["action"],
        "score":       decision["score"],
        "attack_type": decision["attack_type"],
        "fp_id":       decision["fp_id"],
        "is_known_fp": decision["is_known_fp"],
        "signals":     decision["signals"],
        "login_success": False,
    }
    col_events.insert_one(event)

    # Block immediately
    if decision["http_code"] == 403:
        return jsonify({
            "error": "Access denied — suspicious activity detected",
            "strix": {
                "score":       round(decision["score"] * 100),
                "action":      "block",
                "attack_type": decision["attack_type"],
                "fp_id":       decision["fp_id"],
            }
        }), 403

    # ── Authenticate ──────────────────────────────────────────────────────────
    user = col_users.find_one({"email": email})

    if user and bcrypt.checkpw(pwd.encode(), user["password"]):
        col_events.update_one({"_id": event.get("_id")}, {"$set": {"login_success": True}})
        return jsonify({
            "message": "Login successful",
            "user": {
                "id":         str(user["_id"]),
                "name":       user["name"],
                "email":      user["email"],
                "balance":    user.get("balance", 0),
                "account_no": user.get("account_no", ""),
            },
            "strix": {
                "score":       round(decision["score"] * 100),
                "action":      decision["action"],
                "attack_type": decision["attack_type"],
                "fp_id":       decision["fp_id"],
            }
        }), 200
    else:
        return jsonify({
            "error": "Invalid credentials",
            "strix": {
                "score":  round(decision["score"] * 100),
                "action": decision["action"],
            }
        }), 401


# ═══════════════════════════════════════════════════════════════════════════════
# USER
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/user/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = col_users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "id":         str(user["_id"]),
            "name":       user["name"],
            "email":      user["email"],
            "balance":    user.get("balance", 0),
            "account_no": user.get("account_no", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/users/search", methods=["GET"])
def search_users():
    query = request.args.get("email", "").lower().strip()
    if len(query) < 3:
        return jsonify([])
    results = col_users.find(
        {"email": {"$regex": query, "$options": "i"}},
        {"password": 0}
    ).limit(5)
    return jsonify([{
        "id":    str(u["_id"]),
        "name":  u["name"],
        "email": u["email"],
    } for u in results])


# ═══════════════════════════════════════════════════════════════════════════════
# WALLET
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/wallet/add", methods=["POST"])
def add_money():
    data    = request.json
    user_id = data.get("user_id")
    amount  = float(data.get("amount", 0))

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    if amount > 100000:
        return jsonify({"error": "Maximum add limit is ₹1,00,000"}), 400

    try:
        user = col_users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_balance = user.get("balance", 0) + amount
        col_users.update_one({"_id": ObjectId(user_id)}, {"$set": {"balance": new_balance}})

        txn = {
            "txn_id":    "TXN" + str(uuid.uuid4())[:8].upper(),
            "type":      "credit",
            "amount":    amount,
            "from_name": "Wallet Top-up",
            "to_name":   user["name"],
            "note":      "Added to wallet",
            "timestamp": datetime.utcnow().isoformat(),
            "status":    "success",
            "user_id":   user_id,
        }
        col_txns.insert_one(txn)

        return jsonify({
            "message":     "Money added successfully",
            "new_balance": new_balance,
            "txn_id":      txn["txn_id"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wallet/send", methods=["POST"])
def send_money():
    data      = request.json
    sender_id = data.get("sender_id")
    to_email  = data.get("to_email", "").lower().strip()
    amount    = float(data.get("amount", 0))
    note      = data.get("note", "")

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        sender    = col_users.find_one({"_id": ObjectId(sender_id)})
        recipient = col_users.find_one({"email": to_email})

        if not sender:
            return jsonify({"error": "Sender not found"}), 404
        if not recipient:
            return jsonify({"error": "Recipient not found. Check the email address."}), 404
        if str(sender["_id"]) == str(recipient["_id"]):
            return jsonify({"error": "Cannot send money to yourself"}), 400
        if sender.get("balance", 0) < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        new_sender_bal    = sender["balance"] - amount
        new_recipient_bal = recipient.get("balance", 0) + amount

        col_users.update_one({"_id": sender["_id"]},    {"$set": {"balance": new_sender_bal}})
        col_users.update_one({"_id": recipient["_id"]}, {"$set": {"balance": new_recipient_bal}})

        txn_id = "TXN" + str(uuid.uuid4())[:8].upper()
        now    = datetime.utcnow().isoformat()

        col_txns.insert_one({
            "txn_id":    txn_id,
            "type":      "debit",
            "amount":    amount,
            "from_name": sender["name"],
            "to_name":   recipient["name"],
            "to_email":  to_email,
            "note":      note or f"Sent to {recipient['name']}",
            "timestamp": now,
            "status":    "success",
            "user_id":   sender_id,
        })

        col_txns.insert_one({
            "txn_id":    txn_id,
            "type":      "credit",
            "amount":    amount,
            "from_name": sender["name"],
            "to_name":   recipient["name"],
            "note":      note or f"Received from {sender['name']}",
            "timestamp": now,
            "status":    "success",
            "user_id":   str(recipient["_id"]),
        })

        return jsonify({
            "message":        "Money sent successfully",
            "txn_id":         txn_id,
            "new_balance":    new_sender_bal,
            "recipient_name": recipient["name"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/transactions/<user_id>", methods=["GET"])
def get_transactions(user_id):
    try:
        page  = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 20))
        skip  = (page - 1) * limit

        result = list(col_txns.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit))

        total = col_txns.count_documents({"user_id": user_id})

        return jsonify({"transactions": result, "total": total, "page": page})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ═══════════════════════════════════════════════════════════════════════════════
# STRIX DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/strix/stats", methods=["GET"])
def strix_stats():
    try:
        total   = col_decisions.count_documents({})
        blocked = col_decisions.count_documents({"action": "block"})
        captcha = col_decisions.count_documents({"action": "captcha"})
        allowed = col_decisions.count_documents({"action": "allow"})

        suspicious_ips = len(col_decisions.distinct(
            "ip", {"action": {"$in": ["block", "captcha"]}}
        ))

        bot_pct = round((blocked + captcha) / total * 100, 1) if total > 0 else 0

        five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        active_threats = col_decisions.count_documents({
            "action":    "block",
            "timestamp": {"$gte": five_min_ago}
        })

        return jsonify({
            "total":           total,
            "blocked":         blocked,
            "captcha":         captcha,
            "allowed":         allowed,
            "suspicious_ips":  suspicious_ips,
            "bot_traffic_pct": bot_pct,
            "active_threats":  active_threats,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/strix/decisions", methods=["GET"])
def strix_decisions_route():
    try:
        limit  = int(request.args.get("limit", 100))
        result = list(col_decisions.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/strix/fingerprints", methods=["GET"])
def strix_fingerprints_route():
    try:
        limit  = int(request.args.get("limit", 50))
        result = list(col_fingerprints.find({}, {"_id": 0}).sort("last_seen", -1).limit(limit))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Legacy event route (keep for backward compat) ─────────────────────────────
@app.route("/api/strix/events", methods=["GET"])
def strix_events():
    try:
        limit  = int(request.args.get("limit", 50))
        result = list(col_events.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True)