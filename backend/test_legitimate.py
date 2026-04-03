"""Test legitimate user login after fixes"""
import requests
import json

TARGET_URL = "http://localhost:5000/api/login"

# Simulate a LEGITIMATE manual login
payload = {
    "email": "valid_user@example.com",
    "password": "correct_password",
    "time_to_submit": 35000,  # 35 seconds (realistic human time)
    "keystroke_intervals": [80, 150, 120, 95, 200, 110, 85, 1200, 120, 95, 110, 100],  # high variance
    "mouse_move_count": 45,  # good mouse movement
    "password_pasted": False,
    "field_focus_count": 3,
    "js_enabled": True,
}

try:
    r = requests.post(TARGET_URL, json=payload, timeout=5)
    result = r.json()
    
    if "strix" in result:
        strix = result["strix"]
        print(f"✓ Legitimate User Login Test")
        print(f"  Risk Score: {strix['score']}")
        print(f"  Action: {strix['action'].upper()}")
        print(f"  Attack Type: {strix['attack_type']}")
        print(f"\n  Layer Scores:")
        for layer, data in strix["layer_scores"].items():
            print(f"    {layer}: {data}")
        print(f"\n  Signals:")
        for sig in strix.get("signals", []):
            print(f"    • {sig}")
            
        if strix["action"] == "allow":
            print("\n✅ SUCCESS: Legitimate user allowed!")
        elif strix["action"] == "captcha":
            print("\n⚠️ NOTICE: Legitimate user required CAPTCHA (check signals)")
        else:
            print("\n❌ ERROR: Legitimate user blocked!")
    else:
        print(f"Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
