"""Simulate fintech app login flow"""
import requests
import json
import random

TARGET_URL = "http://localhost:5000/api/login"

def test_app_login(email, password, varied=True):
    """Simulate app login with app-like keystroke data"""
    
    # App captures keystroke intervals as user types
    if varied:
        # Natural user typing - random intervals
        keystroke_intervals = [
            random.randint(70, 150) for _ in range(len(email))
        ] + [
            random.randint(50, 300),  # pause before password
        ] + [
            random.randint(80, 180) for _ in range(len(password))
        ]
    else:
        keystroke_intervals = []
    
    payload = {
        "email": email,
        "password": password,
        "time_to_submit": random.randint(25000, 45000),  # realistic app fill time
        "keystroke_intervals": keystroke_intervals,
        "mouse_move_count": random.randint(30, 80),  # app users move mouse
        "password_pasted": False,
        "field_focus_count": 2,
        "js_enabled": True,
    }
    
    try:
        r = requests.post(TARGET_URL, json=payload, timeout=5)
        result = r.json()
        
        if "strix" in result:
            strix = result["strix"]
            return {
                "email": email,
                "score": strix["score"],
                "action": strix["action"],
                "attack_type": strix["attack_type"],
                "signals": strix.get("signals", [])[:3]  # first 3 signals
            }
    except Exception as e:
        return {"error": str(e)}

print("=" * 60)
print("FINTECH APP LOGIN TESTS")
print("=" * 60)

# Test 1: Legitimate user with keystroke data
test1 = test_app_login("mayursapkal41@apsit.ed", "mypassword123", varied=True)
print(f"\n✓ Legitimate User (with keystroke capture)")
print(f"  Email: {test1['email']}")
print(f"  Risk Score: {test1['score']}")
print(f"  Action: {test1['action'].upper()}")
print(f"  Attack Type: {test1['attack_type']}")
print(f"  Result: {'✅ ALLOWED' if test1['action'] == 'allow' else '⚠ CAPTCHA' if test1['action'] == 'captcha' else '❌ BLOCKED'}")

# Test 2: Another legitimate user
test2 = test_app_login("user@example.com", "password456", varied=True)
print(f"\n✓ Legitimate User 2 (with keystroke capture)")
print(f"  Email: {test2['email']}")
print(f"  Risk Score: {test2['score']}")
print(f"  Action: {test2['action'].upper()}")
print(f"  Attack Type: {test2['attack_type']}")
print(f"  Result: {'✅ ALLOWED' if test2['action'] == 'allow' else '⚠ CAPTCHA' if test2['action'] == 'captcha' else '❌ BLOCKED'}")
