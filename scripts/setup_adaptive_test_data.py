import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import date, timedelta
import os

async def main():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.lifeos_db
    
    # 1. Get User
    user = await db.users.find_one({"email": "vinti123@gmail.com"})
    if not user:
        print("User not found!")
        return
    uid = user["_id"]
    print(f"User ID: {uid}")
    
    # 2. Insert Template (for Today)
    today = date.today()
    weekday = today.weekday()
    
    await db.routine_templates.delete_many({"user_id": uid})
    await db.routine_templates.insert_one({
        "user_id": uid,
        "name": "Test Routine",
        "days_of_week": [weekday],
        "tasks": [
            {"title": "Morning Run (Template)", "start_time": "06:00", "end_time": "06:30", "metrics": {"target": 5, "unit": "km", "type": "count"}, "priority": 1, "category": "health"}
        ],
        "is_active": True
    })
    print(f"Inserted Routine Template for weekday {weekday}")
    
    # 3. Insert Yesterday's Plan with Incomplete Task
    yesterday = str(today - timedelta(days=1))
    
    # Clean up old plans for yesterday to avoid duplicates
    old_plans = await db.plans.find({"user_id": uid, "date": yesterday}).to_list(None)
    for p in old_plans:
        await db.tasks.delete_many({"plan_id": p["_id"]})
    await db.plans.delete_many({"user_id": uid, "date": yesterday})

    res = await db.plans.insert_one({
        "user_id": uid,
        "date": yesterday,
        "plan_type": "daily",
        "status": "active",
        "summary": "Yesterday's plan (Test Setup)"
    })
    plan_id = res.inserted_id
    
    await db.tasks.insert_one({
        "plan_id": plan_id,
        "title": "Unfinished Business (Carry Over)",
        "status": "pending",
        "priority": 1,
        "category": "work",
        "metrics": {"target": 100, "unit": "pages"},
        "start_time": "10:00", 
        "end_time": "11:00",
        "task_type": "task"
    })
    print(f"Inserted Yesterday's Plan ({yesterday}) with Carry-Over Task")

if __name__ == "__main__":
    asyncio.run(main())
