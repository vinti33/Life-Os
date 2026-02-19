import requests
import time
import sys
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    email = f"test_{int(time.time())}@example.com"
    try:
        # Register
        print(f"Registering user: {email}")
        resp = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": email,
            "password": "password123",
            "name": "Test User"
        })
        if resp.status_code == 200:
            return resp.json()["token"]
        
        print(f"Registration failed: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"Auth failed: {e}")
        return None

def test_chat(token):
    headers = {"Authorization": f"Bearer {token}"}
    msg = "add task Buy Milk at 5pm"
    
    try:
        print(f"Sending chat message: '{msg}'")
        resp = requests.post(f"{BASE_URL}/chat/message", json={"message": msg}, headers=headers)
        if resp.status_code != 200:
            print(f"Chat failed: {resp.status_code} {resp.text}")
            return False
            
        data = resp.json()
        print(f"Chat Response: {json.dumps(data, indent=2)}")
        
        # Verify ChatbotAgent fix (No ID in payload)
        actions = data.get("actions", [])
        if actions:
            payload = actions[0].get("payload", {})
            if "id" in payload:
                print("FAIL: ChatbotAgent still expects ID in payload!")
                return False
            if payload.get("title") == "Buy Milk":
                print("PASS: ChatbotAgent recognized intent correctly.")
            else:
                print("FAIL: ChatbotAgent payload mismatch.")
                return False
        else:
            print("FAIL: No actions returned.")
            return False
            
        return True
    except Exception as e:
        print(f"Chat test error: {e}")
        return False

if __name__ == "__main__":
    token = login()
    if not token:
        print("Login failed")
        sys.exit(1)
        
    print("Login successful. Testing Agents...")
    if test_chat(token):
        print("Agents Test Passed!")
    else:
        print("Agents Test Failed!")
