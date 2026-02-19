
import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from agents.chatbot_agent import ChatbotAgent
from utils.logger import get_logger

# Mock context
context = {
    "current_plan": []
}

async def test_agent():
    print("Initializing ChatbotAgent...")
    agent = ChatbotAgent(context)
    
    messages = [
        "break morning routine into small tasks",
        "Hello",
    ]

    for message in messages:
        print(f"\nTesting message: '{message}'")
        response = await agent.run(message, [])
        
        print(f"--- RESPONSE for '{message}' ---")
        import json
        print(json.dumps(response, indent=2))
        
        # Check logic
        if message == "Hello":
             if response.get("action") is None:
                 print("✅ Action is None for Hello")
             else:
                 print(f"❌ Action is NOT None for Hello: {response.get('action')}")
                 
        if "break" in message:
             if response.get("action") and response["action"]["type"] == "GENERATE_ROUTINE":
                  print("✅ Action is GENERATE_ROUTINE")
             else:
                  print("❌ Failed to map to GENERATE_ROUTINE")

if __name__ == "__main__":
    asyncio.run(test_agent())
