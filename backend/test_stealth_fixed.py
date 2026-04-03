"""Test stealth bot detection after fixes"""
import requests
import json

TARGET_URL = "http://localhost:5000/api/login"

# Simulate a stealth bot attempt (multiple attempts from different IPs)
test_cases = [
    {
        "name": "Stealth Bot Attempt 1",
        "payload": {
            "email": "alice@gmail.com",
            "password": "trypass1",
            "time_to_submit": 12000,
            "keystroke_intervals": [95, 110, 100, 92, 105, 98, 88, 520, 105, 95, 108, 100],
            "mouse_move_count": 28,
            "password_pasted": False,
            "field_focus_count": 2,
            "js_enabled": True,
        },
        "ip": "10.15.100.50"
    },
    {
        "name": "Stealth Bot Attempt 2",  
        "payload": {
            "email": "bob@yahoo.com",
            "password": "trypass2",
            "time_to_submit": 14000,
            "keystroke_intervals": [98, 105, 102, 94, 108, 100, 90, 550, 102, 98, 105, 102],
            "mouse_move_count": 25,
            "password_pasted": False,
            "field_focus_count": 2,
            "js_enabled": True,
        },
        "ip": "10.20.200.75"
    },
]

for test in test_cases:
    try:
        headers = {"X-Forwarded-For": test["ip"]}
        r = requests.post(TARGET_URL, json=test["payload"], headers=headers, timeout=5)
        result = r.json()
        
        if "strix" in result:
            strix = result["strix"]
            print(f"\n{test['name']}")
            print(f"  IP: {test['ip']}")
            print(f"  Risk Score: {strix['score']}")
            print(f"  Action: {strix['action'].upper()}")
            print(f"  Attack Type: {strix['attack_type']}")
            
            if strix['action'] in ['captcha', 'block']:
                print(f"  ✅ CAUGHT - Stealth bot detected!")
            else:
                print(f"  ❌ MISSED - Stealth bot got through!")
    except Exception as e:
        print(f"  Error: {e}")
