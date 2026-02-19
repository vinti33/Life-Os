
import asyncio
import os
import sys
import logging
from config import settings

# Setup logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
log = logging.getLogger("debug_compare")

from agents.chatbot_agent import ChatbotAgent
from agents.planner_agent import PlannerAgent
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models import User, UserProfile

async def init_db():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    await init_beanie(database=client.lifeos, document_models=[User, "models.Plan", "models.Task", "models.UserProfile", "models.Feedback", "models.Pattern"])
    return client

async def test_compare():
    print(f"--- Environment ---")
    print(f"OPENAI_BASE_URL: {settings.OPENAI_BASE_URL}")
    print(f"AI_MODEL: {settings.AI_MODEL}")
    
    # 1. Test Chatbot Agent (known good?)
    print("\n--- Testing ChatbotAgent ---")
    chatbot = ChatbotAgent({})
    try:
        # Chatbot fallback triggers LLM
        res = await chatbot._handle_llm_fallback("break morning routine")
        print("✅ ChatbotAgent success!")
    except Exception as e:
        print(f"❌ ChatbotAgent failed: {e}")

    # 2. Test Planner Agent
    print("\n--- Testing PlannerAgent ---")
    planner = PlannerAgent()
    
    # Mock data
    profile = {"wake_time": "07:00", "sleep_time": "23:00", "role": "Student"}
    
    # We call the internal _call_llm directly to skip business logic and test connectivity/payload
    prompt = "Test prompt: reply with JSON { 'test': 'ok' }"
    try:
        print(f"PlannerAgent calling {planner.base_url}...")
        res = await planner._call_llm(prompt)
        print("✅ PlannerAgent success!")
        print(res)
    except Exception as e:
        print(f"❌ PlannerAgent failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_compare())
