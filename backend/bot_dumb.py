"""
bot_dumb.py — Dumb Bot Attack
==============================
The most obvious type of bot.
- Fills the honeypot field (instant detection)
- Submits in under 400ms
- No mouse movement, no keystrokes
- Pastes credentials directly
- Runs from known datacenter/proxy IPs

Expected Strix outcome: BLOCK | Score 85–100
"""

import requests
import random
import time
import threading

TARGET_URL = "http://localhost:5000/api/login"

CREDENTIALS = [
    ("alice@gmail.com",     "password123"),
    ("bob@yahoo.com",       "123456"),
    ("charlie@hotmail.com", "qwerty"),
    ("diana@gmail.com",     "letmein"),
    ("eve@outlook.com",     "monkey"),
    ("frank@gmail.com",     "dragon"),
    ("grace@icloud.com",    "master"),
    ("henry@gmail.com",     "login"),
    ("irene@yahoo.com",     "hello"),
    ("jack@gmail.com",      "abc123"),
]

# Known proxy / datacenter IPs — will be caught by network layer too
FAKE_IPS = [
    "185.220.101.5",   # known Tor exit node
    "89.248.167.131",  # known proxy
    "45.33.32.156",    # DigitalOcean
    "193.142.146.35",  # datacenter
    "171.25.193.20",   # known VPN
]

BLOCKED = 0
TOTAL   = 0
LOCK    = threading.Lock()

def attack_once():
    global BLOCKED, TOTAL

    email, pwd = random.choice(CREDENTIALS)
    fake_ip    = random.choice(FAKE_IPS)

    headers = {
        "X-Forwarded-For": fake_ip,
        "User-Agent":      "python-requests/2.28.0"  # dead giveaway
    }

    payload = {
        "email":              email,
        "password":           pwd,
        # ── Behavioral signals (all wrong) ──
        "time_to_submit":     random.randint(80, 350),  # impossibly fast
        "keystroke_intervals": [],                       # zero keystrokes
        "mouse_move_count":   0,                         # zero mouse movement
        "password_pasted":    True,                      # pasted
        "field_focus_count":  0,                         # never focused fields
        "js_enabled":         True,
        # ── HONEYPOT filled ──
        "phone":              "1234567890",
    }

    try:
        r = requests.post(TARGET_URL, json=payload, headers=headers, timeout=10)
        with LOCK:
            TOTAL += 1
            score  = r.json().get("strix", {}).get("score", "?")
            action = r.json().get("strix", {}).get("action", "?")
            if r.status_code == 403:
                BLOCKED += 1
                print(f"[BLOCKED] {fake_ip:20s} -> {email:30s} | score: {score} | {action}")
            else:
                print(f"[PASSED]  {fake_ip:20s} -> {email:30s} | score: {score} | {action}")
    except Exception as e:
        with LOCK: TOTAL += 1
        print(f"[ERR] {e}")

def run(total=40, delay=0.2):
    print("=" * 60)
    print("  DUMB BOT ATTACK — fills honeypot, instant submit")
    print(f"  Sending {total} requests | Expected: BLOCK 85-100")
    print("=" * 60)

    threads = [threading.Thread(target=attack_once) for _ in range(total)]
    for t in threads:
        t.start()
        time.sleep(delay)
    for t in threads:
        t.join()

    print(f"\n  DONE | Total: {TOTAL} | Blocked: {BLOCKED} | Passed: {TOTAL - BLOCKED}")
    print("=" * 60)

if __name__ == "__main__":
    run(total=40, delay=0.2)