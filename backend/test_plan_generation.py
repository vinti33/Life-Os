#!/usr/bin/env python3
"""
Test script to verify AI plan generation is working correctly.
This tests the full flow: authentication -> plan generation
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_plan_generation():
    """Test the plan generation endpoint"""
    print("=" * 60)
    print("Testing AI Plan Generation")
    print("=" * 60)
    
    # Step 1: Login to get auth token
    print("\n1. Authenticating...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try to login (you may need to adjust credentials)
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        
        try:
            login_response = await client.post(
                f"{BASE_URL}/auth/login",
                data=login_data
            )
            
            if login_response.status_code != 200:
                print(f"   ⚠️  Login failed (Status {login_response.status_code})")
                print(f"   Note: You may need to create a test user first")
                print(f"   Proceeding with plan generation test anyway...")
                token = None
            else:
                token_data = login_response.json()
                token = token_data.get("access_token")
                print(f"   ✓ Login successful")
        except Exception as e:
            print(f"   ⚠️  Login error: {e}")
            print(f"   Proceeding with plan generation test anyway...")
            token = None
        
        # Step 2: Test plan generation
        print("\n2. Testing Plan Generation...")
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            plan_response = await client.post(
                f"{BASE_URL}/plan/generate",
                params={"context": "Plan my day for maximum productivity"},
                headers=headers,
                timeout=30.0
            )
            
            print(f"   Status Code: {plan_response.status_code}")
            
            if plan_response.status_code == 200:
                plan_data = plan_response.json()
                print(f"   ✓ Plan generation successful!")
                print(f"\n   Plan Summary: {plan_data.get('summary', 'N/A')}")
                print(f"   Number of Tasks: {len(plan_data.get('tasks', []))}")
                
                if plan_data.get('tasks'):
                    print(f"\n   Sample Tasks:")
                    for i, task in enumerate(plan_data['tasks'][:3], 1):
                        print(f"      {i}. {task.get('title', 'N/A')} ({task.get('category', 'N/A')})")
                
                if plan_data.get('clarification_questions'):
                    print(f"\n   Clarification Questions:")
                    for q in plan_data['clarification_questions']:
                        print(f"      - {q}")
                
                print(f"\n   ✅ AI PLAN FORMATION IS WORKING!")
                return True
            else:
                print(f"   ❌ Plan generation failed")
                print(f"   Response: {plan_response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error during plan generation: {e}")
            return False

if __name__ == "__main__":
    print("\n🤖 LifeOS AI Plan Formation Test\n")
    success = asyncio.run(test_plan_generation())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: AI plan formation is working correctly!")
    else:
        print("❌ TEST FAILED: Check the errors above")
    print("=" * 60 + "\n")
