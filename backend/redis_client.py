import redis
from config import settings

class RedisClient:
    def __init__(self):
        # We use from_url to handle the redis:// syntax from settings
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_client(self):
        return self.client

# Global instance
cache = RedisClient()

def get_cache():
    return cache.get_client()
