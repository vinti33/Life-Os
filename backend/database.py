import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import settings

# Import models here to register them with Beanie
# We will update these imports once models.py is rewritten, 
# but for now we put placeholders or expect models module.
# To avoid circular imports, we might need to import inside the function 
# or ensure models.py doesn't import database.py eagerly.

async def init_db():
    # Create Motor Client
    client = AsyncIOMotorClient(settings.MONGO_URL)
    
    # Initialize Beanie with the specific database
    # Assuming the DB name is the last part of MONGO_URL, but Motor URL 
    # usually specifies it or we pick a default.
    # settings.MONGO_URL is "mongodb://localhost:27118". 
    # We'll use a specific db name "lifeos_db".
    
    # We need to import the document models dynamically or from a centralized place
    from models import User, UserProfile, Plan, Task, Feedback, Pattern, LongTermProgress, ChatSession, ChatMessage, UserMemory, Transaction, Budget, TaskCompletion, RoutineTemplate
    
    await init_beanie(
        database=client.lifeos_db,
        document_models=[
            User,
            UserProfile,
            Plan,
            Task,
            Feedback,
            Pattern,
            LongTermProgress,
            ChatSession,
            UserMemory,
            Transaction,
            Budget,
            TaskCompletion,
            RoutineTemplate
        ]
    )
