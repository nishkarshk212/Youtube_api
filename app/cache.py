import json
import asyncio
from typing import Optional, Any
from loguru import logger
from app.config import settings
import redis.asyncio as redis


class CacheManager:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.enabled = settings.ENABLE_CACHE
        self.ttl = settings.CACHE_TTL

    async def connect(self):
        """Connect to Redis"""
        if not self.enabled:
            logger.info("Cache is disabled")
            return

        try:
            self.redis = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.enabled = False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis cache")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.setex(
                key,
                ttl or self.ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    async def increment(self, key: str) -> int:
        """Increment counter"""
        if not self.enabled or not self.redis:
            return 0

        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.error(f"Cache increment error: {str(e)}")
            return 0

    async def sadd(self, key: str, value: str) -> bool:
        """Add value to Redis set"""
        if not self.enabled or not self.redis:
            return False

        try:
            return await self.redis.sadd(key, value)
        except Exception as e:
            logger.error(f"Cache sadd error: {str(e)}")
            return False

    async def srem(self, key: str, value: str) -> bool:
        """Remove value from Redis set"""
        if not self.enabled or not self.redis:
            return False

        try:
            return await self.redis.srem(key, value)
        except Exception as e:
            logger.error(f"Cache srem error: {str(e)}")
            return False

    async def smembers(self, key: str) -> list:
        """Get all members of Redis set"""
        if not self.enabled or not self.redis:
            return []

        try:
            return await self.redis.smembers(key)
        except Exception as e:
            logger.error(f"Cache smembers error: {str(e)}")
            return []

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.redis:
            return {"enabled": False}

        try:
            info = await self.redis.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
cache = CacheManager()
