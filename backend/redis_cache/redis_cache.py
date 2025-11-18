"""
Redis Cache Client for API Response Caching

Provides:
- Connection pooling for high performance
- Automatic serialization/deserialization (JSON)
- TTL-based expiration
- Cache invalidation strategies
- Health check and stats
- Async/await support
"""

import json
import logging
import os
from typing import Any, Optional, Union

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool
from redis.exceptions import ConnectionError, RedisError, TimeoutError

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Async Redis cache client with connection pooling.

    Features:
    - Connection pool management
    - JSON serialization for complex objects
    - TTL support
    - Pattern-based invalidation
    - Health monitoring
    - Graceful degradation (logs errors, doesn't crash)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis cache client.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number (0-15)
            password: Redis password (if required)
            max_connections: Maximum connection pool size
            decode_responses: Auto-decode bytes to strings
        """
        self.host = host
        self.port = port
        self.db = db

        # Create connection pool
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses,
        )

        self._redis: Optional[aioredis.Redis] = None
        self._is_connected = False

    async def connect(self) -> None:
        """
        Establish Redis connection.

        Raises:
            ConnectionError: If unable to connect to Redis
        """
        try:
            self._redis = aioredis.Redis(connection_pool=self.pool)
            # Test connection
            await self._redis.ping()
            self._is_connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port} (db={self.db})")
        except (ConnectionError, TimeoutError) as e:
            self._is_connected = False
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection and cleanup pool."""
        if self._redis:
            await self._redis.close()
            await self.pool.disconnect()
            self._is_connected = False
            logger.info("Disconnected from Redis")

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value (deserialized from JSON) or default
        """
        if not self._is_connected:
            logger.warning("Redis not connected, returning default value")
            return default

        try:
            value = await self._redis.get(key)
            if value is None:
                return default

            # Deserialize JSON
            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error getting key '{key}': {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected:
            logger.warning("Redis not connected, skipping cache set")
            return False

        try:
            # Serialize to JSON
            serialized = json.dumps(value)

            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)

            return True
        except (RedisError, json.JSONEncodeError, TypeError) as e:
            logger.error(f"Error setting key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if not found or error
        """
        if not self._is_connected:
            logger.warning("Redis not connected, skipping delete")
            return False

        try:
            result = await self._redis.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Error deleting key '{key}': {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*", "cache:api:*")

        Returns:
            Number of keys deleted

        Example:
            await cache.delete_pattern("api:v1:users:*")
        """
        if not self._is_connected:
            logger.warning("Redis not connected, skipping pattern delete")
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern '{pattern}'")
                return deleted

            return 0
        except RedisError as e:
            logger.error(f"Error deleting pattern '{pattern}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            return await self._redis.exists(key) > 0
        except RedisError as e:
            logger.error(f"Error checking key existence '{key}': {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time on a key.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            True if expiration was set, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            return await self._redis.expire(key, ttl)
        except RedisError as e:
            logger.error(f"Error setting expiration on '{key}': {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Get remaining time-to-live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self._is_connected:
            return -2

        try:
            return await self._redis.ttl(key)
        except RedisError as e:
            logger.error(f"Error getting TTL for '{key}': {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter key.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment, or None on error
        """
        if not self._is_connected:
            return None

        try:
            return await self._redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Error incrementing key '{key}': {e}")
            return None

    async def clear(self) -> bool:
        """
        Clear all keys in the current database.

        WARNING: This deletes ALL keys in the database!

        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            await self._redis.flushdb()
            logger.warning(f"Cleared all keys from Redis db={self.db}")
            return True
        except RedisError as e:
            logger.error(f"Error clearing database: {e}")
            return False

    async def ping(self) -> bool:
        """
        Ping Redis server to check health.

        Returns:
            True if server responds, False otherwise
        """
        if not self._redis:
            return False

        try:
            return await self._redis.ping()
        except RedisError as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        if not self._is_connected:
            return {
                "connected": False,
                "error": "Not connected to Redis",
            }

        try:
            info = await self._redis.info("stats")
            keyspace = await self._redis.info("keyspace")

            # Get database stats
            db_info = keyspace.get(f"db{self.db}", {})
            keys_count = db_info.get("keys", 0) if isinstance(db_info, dict) else 0

            return {
                "connected": True,
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "keys": keys_count,
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0),
                ),
            }
        except RedisError as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "connected": True,
                "error": str(e),
            }

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


# ============================================================================
# Global Cache Instance
# ============================================================================

_global_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """
    Get global Redis cache instance.

    Reads configuration from environment variables:
    - REDIS_HOST (default: localhost)
    - REDIS_PORT (default: 6379)
    - REDIS_DB (default: 0)
    - REDIS_PASSWORD (optional)
    - REDIS_MAX_CONNECTIONS (default: 50)

    Returns:
        RedisCache instance
    """
    global _global_cache

    if _global_cache is None:
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))
        password = os.getenv("REDIS_PASSWORD")
        max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

        _global_cache = RedisCache(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
        )

    return _global_cache


async def init_redis_cache() -> RedisCache:
    """
    Initialize and connect to Redis cache.

    Call this during FastAPI startup.

    Returns:
        Connected RedisCache instance
    """
    cache = get_redis_cache()
    await cache.connect()
    return cache


async def close_redis_cache() -> None:
    """
    Close Redis connection.

    Call this during FastAPI shutdown.
    """
    global _global_cache
    if _global_cache:
        await _global_cache.disconnect()
        _global_cache = None


# ============================================================================
# Cache Key Helpers
# ============================================================================


def make_cache_key(prefix: str, *parts: Union[str, int]) -> str:
    """
    Generate a cache key from parts.

    Args:
        prefix: Key prefix (e.g., "api", "user", "query")
        *parts: Additional key components

    Returns:
        Cache key string

    Example:
        >>> make_cache_key("api", "v1", "users", 123)
        'api:v1:users:123'
    """
    return ":".join([prefix] + [str(p) for p in parts])
