import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def list_users():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27118")
    client = AsyncIOMotorClient(mongo_url)
    
    # List databases
    dbs = await client.list_database_names()
    print(f"Databases: {dbs}")
    
    for db_name in ["lifeos", "lifeos_db"]:
        if db_name in dbs:
            db = client[db_name]
            users = await db.users.find().to_list(10)
            print(f"--- DB: {db_name} ---")
            for user in users:
                print(f"Name: {user.get('name')}, Email: {user.get('email')}")
    client.close()

if __name__ == "__main__":
    asyncio.run(list_users())
