import asyncio
from models import User, Plan, Task, TaskCompletion, TaskStatus, PlanType
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import date
from typing import List

async def seed():
    # Correct URL and User imports
    client = AsyncIOMotorClient("mongodb://localhost:27118")
    # Must match database.py models list
    from models import User, UserProfile, Plan, Task, Feedback, Pattern, LongTermProgress, ChatSession, UserMemory, Transaction, Budget, TaskCompletion
    
    await init_beanie(database=client.lifeos_db, document_models=[User, UserProfile, Plan, Task, Feedback, Pattern, LongTermProgress, ChatSession, UserMemory, Transaction, Budget, TaskCompletion])
    
    # Get ANY user
    user = await User.find_one()
    if not user:
        print("No users found at all! Creating one...")
        # Create a user if none exists
        from models import User
        user = User(name="Test User", email="test@lifeos.ai", hashed_password="hashed_password")
        await user.insert()
        print(f"Created user: {user.email}")
    else:
        print(f"Seeding for user: {user.email}")

    today = str(date.today())
    
    # Check Plan
    plan = await Plan.find_one(Plan.user_id == user.id, Plan.date == today)
    if not plan:
        plan = Plan(user_id=user.id, date=today, plan_type=PlanType.DAILY)
        await plan.insert()
        print("Created Plan")
        
    # Check Completion
    completions = await TaskCompletion.find(
        TaskCompletion.user_id == user.id,
        TaskCompletion.date >= "2026-01-01"
    ).to_list()
    
    if len(completions) < 5:
        # Create some historical data for heatmap
        dates = ["2026-01-15", "2026-02-01", "2026-02-10", "2026-02-14", today]
        from bson import ObjectId
        for d in dates:
             # Just fake a task ID
             tid = ObjectId() 
             c = TaskCompletion(task_id=tid, user_id=user.id, date=d, status=TaskStatus.DONE)
             await c.insert()
             print(f"Inserted completion for {d}")
    else:
         print(f"User already has {len(completions)} completions.")

if __name__ == "__main__":
    asyncio.run(seed())
