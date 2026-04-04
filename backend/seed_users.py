"""
seed_users.py — Seed / reset test users
=========================================
Creates test accounts with real balances.
If the user already exists, it UPDATES their balance and account_no.
Run this: python seed_users.py
"""

from pymongo import MongoClient
import bcrypt, uuid

client = MongoClient("mongodb://localhost:27017/")
db     = client["strixfintech"]
users  = db["users"]

TEST_USERS = [
    {"name": "Alice Johnson",   "email": "alice@gmail.com",     "password": "pass1234",  "balance": 12500.00},
    {"name": "Bob Smith",       "email": "bob@yahoo.com",       "password": "bobby123",  "balance": 8750.50},
    {"name": "Charlie Brown",   "email": "charlie@hotmail.com", "password": "charlie!",  "balance": 3200.00},
    {"name": "Diana Prince",    "email": "diana@gmail.com",     "password": "diana99",   "balance": 25000.00},
    {"name": "Eve Adams",       "email": "eve@outlook.com",     "password": "evepass",   "balance": 5500.75},
    {"name": "Frank Castle",    "email": "frank@gmail.com",     "password": "frank007",  "balance": 9999.00},
    {"name": "Grace Hopper",    "email": "grace@icloud.com",    "password": "graceful",  "balance": 15000.00},
    {"name": "Henry Ford",      "email": "henry@gmail.com",     "password": "henry22",   "balance": 4320.25},
    {"name": "Irene Curie",     "email": "irene@yahoo.com",     "password": "irene456",  "balance": 7800.00},
    {"name": "Jack Sparrow",    "email": "jack@gmail.com",      "password": "jackpass",  "balance": 1200.00},
]

print("Seeding test users...\n")

for u in TEST_USERS:
    existing = users.find_one({"email": u["email"]})
    if existing:
        # ── Update balance + ensure account_no exists ──
        update = {"balance": u["balance"]}
        if not existing.get("account_no"):
            update["account_no"] = str(uuid.uuid4())[:8].upper()
        users.update_one({"email": u["email"]}, {"$set": update})
        print(f"[UPDATED] {u['email']} — Balance reset to ₹{u['balance']:,.2f}")
    else:
        hashed = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt())
        users.insert_one({
            "name":       u["name"],
            "email":      u["email"],
            "password":   hashed,
            "balance":    u["balance"],
            "account_no": str(uuid.uuid4())[:8].upper(),
            "created_at": "2025-01-01T00:00:00",
        })
        print(f"[CREATED] {u['email']} — Balance: ₹{u['balance']:,.2f}")

print("\n✓ Done. All test users ready with correct balances.")