import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import RoutineTemplate, User, UserProfile, Plan, Task, Feedback, Pattern, LongTermProgress, ChatSession, UserMemory, Transaction, Budget, TaskCompletion

async def test_init():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    try:
        await init_beanie(
            database=client.lifeos_db,
            document_models=[
                User, UserProfile, Plan, Task, Feedback, Pattern, 
                LongTermProgress, ChatSession, UserMemory, Transaction, 
                Budget, TaskCompletion, RoutineTemplate
            ]
        )
        print("Initialization Success")
        # Test finding a template
        template = await RoutineTemplate.find_one({})
        print(f"Query Success (Template found: {template is not None})")
    except Exception as e:
        print(f"Initialization Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_init())
