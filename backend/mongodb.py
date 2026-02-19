from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        self.db = self.client.lifeos

    def get_collection(self, name: str):
        return self.db[name]

# Global instance
nosql_db = MongoDB()

async def get_nosql_db():
    return nosql_db.db
