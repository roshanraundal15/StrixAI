"""Test stealth bot detection with 30 accounts"""
import requests
import random

TARGET_URL = "http://localhost:5000/api/login"

# 30 test accounts simulating a stealth bot credential stuffing attack
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
    ("paul@gmail.com",      "trypass16"),
    ("quinn@hotmail.com",   "trypass17"),
    ("rachel@gmail.com",    "trypass18"),
    ("sam@yahoo.com",       "trypass19"),
    ("tina@gmail.com",      "trypass20"),
    ("una@outlook.com",     "trypass21"),
    ("victor@icloud.com",   "trypass22"),
    ("wendy@gmail.com",     "trypass23"),
    ("xavier@hotmail.com",  "trypass24"),
    ("yara@gmail.com",      "trypass25"),
    ("zack@yahoo.com",      "trypass26"),
    ("amy@gmail.com",       "trypass27"),
    ("ben@hotmail.com",     "trypass28"),
    ("cara@gmail.com",      "trypass29"),
    ("dan@outlook.com",     "trypass30"),
]

# Fake IPs for each request (distributed)
FAKE_IPS = [
    f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    for _ in range(30)
]

BLOCKED = 0
CAPTCHA = 0
ALLOWED = 0

print("=" * 70)
print("STEALTH BOT ATTACK SIMULATION - 30 ACCOUNTS")
print("=" * 70)

for i, ((email, pwd), ip) in enumerate(zip(CREDENTIALS, FAKE_IPS), 1):
    payload = {
        "email": email,
        "password": pwd,
        "time_to_submit": random.randint(10000, 16000),  # 10-16 seconds
        "keystroke_intervals": [
            random.randint(90, 110) for _ in range(len(email))
        ] + [random.randint(400, 600)] + [
            random.randint(90, 110) for _ in range(len(pwd))
        ],
        "mouse_move_count": random.randint(20, 35),
        "password_pasted": False,
        "field_focus_count": 2,
        "js_enabled": True,
    }

    try:
        headers = {"X-Forwarded-For": ip}
        r = requests.post(TARGET_URL, json=payload, headers=headers, timeout=5)
        result = r.json()

        if "strix" in result:
            strix = result["strix"]
            score = strix["score"]
            action = strix["action"]

            if action == "block":
                BLOCKED += 1
                status = "[BLOCK]"
            elif action == "captcha":
                CAPTCHA += 1
                status = "[CAPTCHA]"
            else:
                ALLOWED += 1
                status = "[ALLOW]"

            print(f"[{i:2d}/30] {status:10s} | {email:25s} | Score: {score:.3f}")

    except Exception as e:
        print(f"[{i:2d}/30] [ERROR] | {email:25s} - {str(e)}")

print("\n" + "=" * 70)
print("ATTACK DETECTION SUMMARY")
print("=" * 70)
print(f"ALLOWED:  {ALLOWED:2d} ({ALLOWED/30*100:5.1f}%)")
print(f"CAPTCHA:  {CAPTCHA:2d} ({CAPTCHA/30*100:5.1f}%)")
print(f"BLOCKED:  {BLOCKED:2d} ({BLOCKED/30*100:5.1f}%)")
print(f"\nTotal Caught: {CAPTCHA + BLOCKED}/30 ({(CAPTCHA + BLOCKED)/30*100:.1f}%)")

if CAPTCHA + BLOCKED >= 28:
    print(f"\n[EXCELLENT] {CAPTCHA + BLOCKED}/30 attack attempts detected!")
elif CAPTCHA + BLOCKED >= 25:
    print(f"\n[VERY GOOD] {CAPTCHA + BLOCKED}/30 attack attempts detected!")
elif CAPTCHA + BLOCKED >= 20:
    print(f"\n[GOOD] {CAPTCHA + BLOCKED}/30 attack attempts detected")
else:
    print(f"\n[WARNING] Only {CAPTCHA + BLOCKED}/30 attack attempts detected")
