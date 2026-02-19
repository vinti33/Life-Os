import asyncio
from typing import Dict, List, Any
from agents.chatbot_agent import ChatbotAgent
from utils.logger import get_logger

log = get_logger("verification")

# MOCK CONTEXT
MOCK_TASKS = [
    {"id": "1", "title": "Morning Routine", "start_time": "07:00", "end_time": "08:00", "category": "health"},
    {"id": "2", "title": "Work Block", "start_time": "09:00", "end_time": "12:00", "category": "work"},
    {"id": "3", "title": "Lunch", "start_time": "12:00", "end_time": "13:00", "category": "personal"},
]

async def verify_reschedule_flow():
    print("=== Verifying Replanning Logic ===")
    
    # Initialize Agent with Context
    context = {"current_plan": MOCK_TASKS}
    agent = ChatbotAgent(context)

    # Test Case 1: Reschedule "Lunch" to 1pm
    msg = "Reschedule Lunch to 1pm"
    print(f"\nUser: '{msg}'")
    
    response = await agent.run(msg, MOCK_TASKS)
    
    assert response["type"] == "ACTION_RESPONSE", "Wrong response type"
    action = response["action"]
    
    print(f"Agent Reply: {response['message']}")
    print(f"Action Type: {action['type']}")
    print(f"Payload: {action['payload']}")

    # VERIFICATION: Should be GENERATE_ROUTINE, not UPDATE_TASK
    if action["type"] == "GENERATE_ROUTINE":
        print("✅ SUCCESS: Smart Replanning Triggered (GENERATE_ROUTINE)")
        if "Reschedule task 'Lunch'" in action["payload"]["context"]:
             print("✅ Context correctly captured instructions")
        else:
             print("❌ Context missing instructions")
    else:
        print(f"❌ FAILURE: Expected GENERATE_ROUTINE, got {action['type']}")

    # Test Case 2: Add Task
    msg = "Add gym at 6pm"
    print(f"\nUser: '{msg}'")
    response = await agent.run(msg, MOCK_TASKS)
    action = response["action"]
    
    if action["type"] == "GENERATE_ROUTINE":
         print("✅ SUCCESS: Add Task triggered Smart Replanning")
    else:
         print(f"❌ FAILURE: Add Task got {action['type']}")

if __name__ == "__main__":
    asyncio.run(verify_reschedule_flow())
