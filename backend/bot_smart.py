"""
bot_smart.py — Smart Bot Attack
=================================
A more sophisticated bot that:
- AVOIDS the honeypot field (leaves it empty)
- Adds some fake keystroke intervals
- Adds small mouse movement count
- Still submits too fast for a real human
- Uses residential-looking IPs (not known proxies)
- Targets many different accounts (credential stuffing pattern)

Expected Strix outcome: BLOCK or CAPTCHA | Score 45–80
The session layer and behavioral layer catch this one.
"""

import requests
import random
import time
import threading

TARGET_URL = "http://localhost:5000/api/login"

CREDENTIALS = [
    ("alice@gmail.com",     "pass1234"),
    ("bob@yahoo.com",       "bobby123"),
    ("charlie@hotmail.com", "charlie!"),
    ("diana@gmail.com",     "diana99"),
    ("eve@outlook.com",     "evepass"),
    ("frank@gmail.com",     "frank007"),
    ("grace@icloud.com",    "graceful"),
    ("henry@gmail.com",     "henry22"),
    ("irene@yahoo.com",     "irene456"),
    ("jack@gmail.com",      "jackpass"),
    ("karen@gmail.com",     "karen321"),
    ("leo@hotmail.com",     "leo2024"),
    ("mia@gmail.com",       "mia1234"),
    ("noah@gmail.com",      "noah999"),
    ("olivia@yahoo.com",    "olivia11"),
]

# Residential-looking IPs — NOT in known proxy lists
FAKE_IPS = [
    "203.0.113.45",
    "198.51.100.22",
    "192.0.2.178",
    "203.0.113.99",
    "198.51.100.77",
    "203.0.113.12",
    "192.0.2.55",
    "203.0.113.200",
]

BLOCKED  = 0
CAPTCHA  = 0
ALLOWED  = 0
TOTAL    = 0
LOCK     = threading.Lock()

def fake_keystrokes(n=6):
    """Generate fake but suspiciously uniform keystroke intervals."""
    base = random.randint(60, 100)
    # Bot tries to add small variation but it's too uniform
    return [base + random.randint(-5, 5) for _ in range(n)]

def attack_once():
    global BLOCKED, CAPTCHA, ALLOWED, TOTAL

    email, pwd = random.choice(CREDENTIALS)
    fake_ip    = random.choice(FAKE_IPS)

    headers = {
        "X-Forwarded-For": fake_ip,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    payload = {
        "email":    email,
        "password": pwd,
        # ── Behavioral signals (partially faked) ──
        "time_to_submit":      random.randint(1500, 3500),  # still too fast
        "keystroke_intervals": fake_keystrokes(),            # too uniform
        "mouse_move_count":    random.randint(2, 8),         # minimal mouse
        "password_pasted":     True,                         # still pasted
        "field_focus_count":   1,                            # only one focus
        "js_enabled":          True,
        # ── HONEYPOT left empty (smart bot avoids it) ──
        "phone":               "",
    }

    try:
        r = requests.post(TARGET_URL, json=payload, headers=headers, timeout=10)
        with LOCK:
            TOTAL += 1
            data   = r.json()
            score  = data.get("strix", {}).get("score", "?")
            action = data.get("strix", {}).get("action", "?")

            if r.status_code == 403:
                BLOCKED += 1
                print(f"[BLOCKED] {fake_ip:20s} -> {email:28s} | score: {score}")
            elif action == "captcha":
                CAPTCHA += 1
                print(f"[CAPTCHA] {fake_ip:20s} -> {email:28s} | score: {score}")
            else:
                ALLOWED += 1
                print(f"[SLIPPED] {fake_ip:20s} -> {email:28s} | score: {score}")
    except Exception as e:
        with LOCK: TOTAL += 1
        print(f"[ERR] {e}")

def run(total=40, delay=0.4):
    print("=" * 60)
    print("  SMART BOT ATTACK — avoids honeypot, fakes behavior")
    print(f"  Sending {total} requests | Expected: BLOCK/CAPTCHA 45-80")
    print("=" * 60)

    threads = [threading.Thread(target=attack_once) for _ in range(total)]
    for t in threads:
        t.start()
        time.sleep(delay)
    for t in threads:
        t.join()

    print(f"\n  DONE | Total: {TOTAL} | Blocked: {BLOCKED} | CAPTCHA: {CAPTCHA} | Slipped: {ALLOWED}")
    print("=" * 60)

if __name__ == "__main__":
    run(total=40, delay=0.4)