
import asyncio
import os
import sys
from datetime import date

# Add current directory to path
sys.path.append(os.getcwd())

from services.planning_service import PlanningService
from models import User
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging
from agents.planner_agent import PlannerAgent
print(f"DEBUG: Loaded PlannerAgent from {PlannerAgent.__module__}")
import inspect
print(f"DEBUG: PlannerAgent file: {inspect.getfile(PlannerAgent)}")

logging.basicConfig(level=logging.INFO)

async def init_db():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    await init_beanie(database=client.lifeos, document_models=[User, "models.Plan", "models.Task", "models.UserProfile", "models.Feedback", "models.Pattern"])
    return client

async def test_plan_generation():
    print(f"Initializing DB with: {settings.MONGO_URL}")
    print(f"Using LLM Endpoint: {settings.OPENAI_BASE_URL}")
    await init_db()
    
    # Get a user (or mock one)
    user = await User.find_one({})
    if not user:
        print("No user found. Creating mock user...")
        user = User(
            email="test@debug.com", 
            name="Debug User",
            hashed_password="mock",
            plan_type="free"
        )
        await user.insert()
        # Create profile too
        from models import UserProfile
        await UserProfile(
            user_id=user.id, 
            work_start_time="09:00", 
            work_end_time="17:00",
            sleep_time="23:00",
            wake_time="07:00",
            energy_levels="medium"
        ).insert()

    print(f"Testing for user {user.id} ({user.email})")
    
    print("Calling create_daily_plan...")
    try:
        # strict timeout to see if it hangs
        plan = await asyncio.wait_for(
            PlanningService.create_daily_plan(
                user.id, 
                str(date.today()),
                context="break morning routine into small tasks"
            ),
            timeout=60 # 60s timeout
        )
        print("✅ Plan generated successfully!")
        print(f"Plan ID: {plan.id}")
        print(f"Summary: {plan.summary}")
    except asyncio.TimeoutError:
        print("❌ Timeout! Plan generation took > 60s")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_plan_generation())
