import asyncio
import json
from agents.chatbot_agent import ChatbotAgent

async def test():
    print("--- Verifying Chatbot Regex Logic (Time Ranges) ---")

    context = {
        "current_plan": [
            {"id": "exist_1", "title": "Deep Work", "start_time": "09:00", "end_time": "11:00"}
        ]
    }
    
    agent = ChatbotAgent(context)

    # Test Case 1: Simple Time
    msg1 = "Add gym at 6pm"
    print(f"\nUser: {msg1}")
    res1 = await agent.send_message(1, msg1)
    print(f"Bot: {res1.get('reply')}")
    print(f"Action: {json.dumps(res1.get('actions'), indent=2)}")

    # Test Case 2: Time Range
    msg2 = "Add breakfast from 07:30 to 09:45"
    print(f"\nUser: {msg2}")
    res2 = await agent.send_message(1, msg2)
    print(f"Bot: {res2.get('reply')}")
    print(f"Action: {json.dumps(res2.get('actions'), indent=2)}")

if __name__ == "__main__":
    asyncio.run(test())
