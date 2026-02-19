"""
LifeOS Caching Layer — Redis-backed Caching Utilities
======================================================
Provides a singleton `RedisCache` and a `@cache` decorator for async functions.
Handles serialization (JSON), TTL management, and key invalidation.
"""

import json
import logging
import inspect
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
from redis.asyncio import Redis, from_url
from config import settings

log = logging.getLogger("cache")


class RedisCache:
    """Singleton wrapper for Redis client."""
    _instance = None

    def __init__(self):
        self.client: Optional[Redis] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisCache()
        return cls._instance

    async def connect(self):
        """Connects to Redis using settings.REDIS_URL."""
        if self.client:
            return
        try:
            self.client = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await self.client.ping()
            log.info(f"Redis connected: {settings.REDIS_URL}")
        except Exception as e:
            log.error(f"Redis connection failed: {e}")
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            log.warning(f"Cache get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        if not self.client:
            return
        try:
            await self.client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            log.warning(f"Cache set failed for {key}: {e}")

    async def delete(self, key: str):
        if not self.client:
            return
        await self.client.delete(key)

    async def flush(self):
        if not self.client:
            return
        await self.client.flushdb()


# Singleton accessor
def get_cache() -> RedisCache:
    return RedisCache.get_instance()


def cache(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache async function results in Redis.
    Key is generated from function name + args + kwargs.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_instance = get_cache()
            if not cache_instance.client:
                return await func(*args, **kwargs)

            # Generate stable key
            # Skip 'self' or 'cls' in args[0] if it's a method
            arg_start = 1 if args and hasattr(args[0], '__class__') else 0
            
            # Serialize args/kwargs safely
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(a) for a in args[arg_start:])
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            # Hash long keys to prevent Redis issues
            key_str = ":".join(key_parts)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_key = f"cache:{key_prefix or func.__name__}:{key_hash}"

            # Try get
            cached_val = await cache_instance.get(cache_key)
            if cached_val is not None:
                log.debug(f"Cache hit: {cache_key}")
                return cached_val

            # Compute and set
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_instance.set(cache_key, result, ttl=ttl)
                log.debug(f"Cache miss (stored): {cache_key}")
            
            return result
        return wrapper
    return decorator
