"""
seed_users.py
─────────────
Creates test user accounts in MongoDB so the bot attack has real targets.
Run once before running bot_attack.py

Usage:  python seed_users.py
"""

import requests

BASE = "http://localhost:5000/api/register"

USERS = [
    {"name": "Alice Johnson",   "email": "alice@gmail.com",     "password": "securepass1"},
    {"name": "Bob Smith",       "email": "bob@yahoo.com",       "password": "mypass999"},
    {"name": "Charlie Brown",   "email": "charlie@hotmail.com", "password": "charlie2024"},
    {"name": "Diana Prince",    "email": "diana@gmail.com",     "password": "wonder123"},
    {"name": "Eve Williams",    "email": "eve@outlook.com",     "password": "evesecret"},
    {"name": "Frank Castle",    "email": "frank@gmail.com",     "password": "punisher9"},
    {"name": "Grace Hopper",    "email": "grace@icloud.com",    "password": "codemaster"},
    {"name": "Henry Ford",      "email": "henry@gmail.com",     "password": "fordpass1"},
    {"name": "Irene Adler",     "email": "irene@yahoo.com",     "password": "irene@007"},
    {"name": "Jack Sparrow",    "email": "jack@gmail.com",      "password": "captainjack"},
]

for u in USERS:
    r = requests.post(BASE, json=u)
    if r.status_code == 201:
        print(f"[OK]  Created: {u['email']}")
    elif r.status_code == 409:
        print(f"[--]  Already exists: {u['email']}")
    else:
        print(f"[ERR] {u['email']} → {r.json()}")

print("\n✓ Done. Test users are ready.")