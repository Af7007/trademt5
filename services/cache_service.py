"""
Redis cache service for optimizing MT5 API calls
"""
import json
import logging
from typing import Optional, Any
from core.config import settings

logger = logging.getLogger(__name__)

# Try to import redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, caching disabled")


class CacheService:
    """Service for caching data in Redis"""

    def __init__(self):
        self.enabled = settings.REDIS_ENABLED and REDIS_AVAILABLE
        self.client: Optional[redis.Redis] = None

        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                self.client.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if not self.enabled or not self.client:
            return False

        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.enabled or not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "symbol:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0

    def flush(self) -> bool:
        """
        Flush all cache

        Returns:
            True if successful
        """
        if not self.enabled or not self.client:
            return False

        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


# Global instance
cache_service = CacheService()
