import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

async def create_debug_user():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27118")
    client = AsyncIOMotorClient(mongo_url)
    db = client.lifeos_db
    
    email = "debug@test.com"
    password = "password123"
    hashed_password = pwd_context.hash(password)
    
    user_data = {
        "name": "DebugUser",
        "email": email,
        "hashed_password": hashed_password,
        "timezone": "UTC"
    }
    
    await db.users.update_one(
        {"email": email},
        {"$set": user_data},
        upsert=True
    )
    print(f"User {email} created/updated with password: {password}")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_debug_user())
