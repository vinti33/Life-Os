#!/usr/bin/env python3
"""
Quick test of chatbot endpoint with curl
"""
import subprocess
import json

print("Testing Chatbot Endpoint")
print("=" * 60)

# Note: This test requires a valid auth token
# For now, let's test if the endpoint is accessible

cmd = [
    "curl", "-X", "POST",
    "http://localhost:8000/api/v1/chat/message",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"message": "Hello, can you help me?"})
]

print("\nSending request to chatbot endpoint...")
print(f"Command: {' '.join(cmd)}\n")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(f"Status Code: {result.returncode}")
    print(f"\nResponse:")
    print(result.stdout)
    
    if result.stderr:
        print(f"\nErrors:")
        print(result.stderr)
        
except subprocess.TimeoutExpired:
    print("Request timed out after 10 seconds")
except Exception as e:
    print(f"Error: {e}")
