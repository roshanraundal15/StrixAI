"""Quick test of stealth bot detection"""
import requests
import json

TARGET_URL = "http://localhost:5000/api/login"

# Simulate a stealth bot attempt
payload = {
    "email": "test@gmail.com",
    "password": "testpass123",
    "time_to_submit": 12000,  # 12 seconds (realistic)
    "keystroke_intervals": [95, 110, 100, 92, 105, 98, 88, 520, 105, 95, 108, 100],  # realistic variance
    "mouse_move_count": 28,  # reasonable mouse movement
    "password_pasted": False,
    "field_focus_count": 2,
    "js_enabled": True,
}

headers = {
    "X-Forwarded-For": "203.0.113.42",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

print("[TEST] Sending stealth bot-like request...")
try:
    response = requests.post(TARGET_URL, json=payload, headers=headers, timeout=5)
    result = response.json()
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if "score" in result:
        print(f"\n✓ RISK SCORE: {result['score']}")
        print(f"✓ ACTION: {result['action'].upper()}")
        if result['action'] == 'block':
            print("✓ SUCCESS: Stealth bot detected and BLOCKED!")
        elif result['action'] == 'captcha':
            print("✓ PARTIAL: Stealth bot flagged for CAPTCHA")
        else:
            print("✗ ISSUE: Stealth bot allowed through")
            
except Exception as e:
    print(f"✗ Error: {e}")
