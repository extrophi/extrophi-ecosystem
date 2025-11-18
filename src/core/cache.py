"""
Cache management module using Valkey (Redis fork).

This module provides a comprehensive caching solution with support for:
    - Key-value caching with TTL
    - Multi-tenant cache isolation
    - Pub/Sub for real-time messaging
    - Atomic operations (increment, etc.)
    - Cache invalidation patterns
    - Connection pooling
    - Graceful error handling

Valkey is a high-performance fork of Redis that maintains full compatibility
while providing enhanced features and performance improvements.

Example:
    Basic caching usage:
        
        from src.core.cache import cache_manager
        
        # Set value with TTL
        await cache_manager.set("user:123", user_data, ttl=3600)
        
        # Get cached value
        user_data = await cache_manager.get("user:123")
        
        # Cache-aside pattern
        user = await cache_manager.get_or_set(
            "user:123",
            lambda: fetch_user_from_db(123),
            ttl=3600
        )

Note:
    All cache keys are automatically prefixed with tenant ID when
    multi-tenancy is enabled, ensuring data isolation.
"""

# Standard library imports
import json
import logging
import pickle
from contextlib import asynccontextmanager
from datetime import timedelta
from enum import Enum
from functools import wraps
from typing import (
    Any, AsyncGenerator, Callable, Coroutine, Dict, List, Optional, 
    Set, TypeVar, Union, cast
)

# Third-party imports
import valkey.asyncio as valkey_async
from pydantic import BaseModel, Field
from valkey.asyncio import Valkey, ConnectionPool
from valkey.asyncio.client import PubSub
from valkey.exceptions import ConnectionError, TimeoutError, ValkeyError

# Local application imports
from src.core.config import settings

# Type variables
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Coroutine[Any, Any, Any]])

# Configure logging
logger = logging.getLogger(__name__)

# Cache constants
DEFAULT_TTL = 300  # 5 minutes
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 0.1  # seconds
LOCK_TIMEOUT = 10  # seconds
SCAN_COUNT = 1000  # Keys per scan iteration


class CacheKeyPrefix(str, Enum):
    """Standard cache key prefixes for different data types."""
    USER = "user"
    SESSION = "session"
    TOKEN = "token"
    VECTOR = "vector"
    SEARCH = "search"
    LOCK = "lock"
    RATE_LIMIT = "rate_limit"
    TEMP = "temp"


class CacheConfig(BaseModel):
    """Cache configuration model."""
    url: str = Field(default=settings.VALKEY_URL, description="Valkey connection URL")
    default_ttl: int = Field(default=settings.CACHE_TTL, description="Default TTL in seconds")
    max_connections: int = Field(default=50, description="Maximum connection pool size")
    socket_timeout: float = Field(default=5.0, description="Socket timeout in seconds")
    socket_connect_timeout: float = Field(default=5.0, description="Connection timeout")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    health_check_interval: int = Field(default=30, description="Health check interval")


class CacheManager:
    """
    Asynchronous cache manager with connection pooling and error handling.
    
    This class provides a high-level interface to Valkey with automatic
    connection management, retries, and multi-tenant support.
    
    Attributes:
        config: Cache configuration
        pool: Connection pool for efficient connection reuse
        _client: Valkey client instance
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache manager with configuration.
        
        Args:
            config: Optional cache configuration (uses defaults if not provided)
        """
        self.config = config or CacheConfig()
        self.pool: Optional[ConnectionPool] = None
        self._client: Optional[Valkey] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        Establish connection to Valkey server.
        
        Creates a connection pool and client instance if not already connected.
        Uses connection pooling for efficient resource management.
        
        Raises:
            ConnectionError: If connection fails after retries
        """
        if self._connected and self._client:
            try:
                # Verify connection is still alive
                await self._client.ping()
                return
            except (ConnectionError, TimeoutError):
                logger.warning("Lost connection to cache, reconnecting...")
                self._connected = False
        
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.config.url,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
                decode_responses=True,  # Return strings instead of bytes
            )
            
            # Create client
            self._client = Valkey(connection_pool=self.pool)
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info("Successfully connected to cache")
            
        except Exception as e:
            logger.error(f"Failed to connect to cache: {e}")
            raise ConnectionError(f"Cache connection failed: {e}")
    
    async def disconnect(self) -> None:
        """
        Close cache connections and cleanup resources.
        
        Properly closes the connection pool to avoid resource leaks.
        """
        if self._client:
            await self._client.close()
            self._client = None
        
        if self.pool:
            await self.pool.disconnect()
            self.pool = None
        
        self._connected = False
        logger.info("Disconnected from cache")
    
    def _make_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """
        Construct cache key with optional tenant prefix.
        
        Args:
            key: Base cache key
            tenant_id: Optional tenant identifier
            
        Returns:
            Formatted cache key with tenant prefix if applicable
        """
        if settings.ENABLE_MULTI_TENANT and tenant_id:
            return f"tenant:{tenant_id}:{key}"
        return key
    
    async def _execute_with_retry(
        self,
        operation: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> Optional[T]:
        """
        Execute cache operation with automatic retry logic.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Operation result or None if all retries fail
        """
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                await self.connect()
                return await operation(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    logger.warning(f"Cache operation failed (attempt {attempt + 1}): {e}")
                    await self.disconnect()
                    continue
                logger.error(f"Cache operation failed after {MAX_RETRY_ATTEMPTS} attempts")
                return None
            except Exception as e:
                logger.error(f"Unexpected cache error: {e}")
                return None
    
    async def get(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            tenant_id: Optional tenant identifier
            default: Default value if key not found
            
        Returns:
            Cached value or default if not found
        """
        full_key = self._make_key(key, tenant_id)
        
        async def _get():
            value = await self._client.get(full_key)
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value
        
        return await self._execute_with_retry(_get)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if dict/list)
            ttl: Time to live in seconds (uses default if not specified)
            tenant_id: Optional tenant identifier
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            True if value was set, False otherwise
        """
        full_key = self._make_key(key, tenant_id)
        ttl = ttl or self.config.default_ttl
        
        # Serialize value
        if isinstance(value, (dict, list, tuple, set)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = str(value)
        
        async def _set():
            return await self._client.set(
                full_key,
                value,
                ex=ttl if ttl > 0 else None,
                nx=nx,
                xx=xx
            )
        
        result = await self._execute_with_retry(_set)
        return bool(result)
    
    async def delete(
        self,
        *keys: str,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Delete one or more keys from cache.
        
        Args:
            *keys: Cache keys to delete
            tenant_id: Optional tenant identifier
            
        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0
        
        full_keys = [self._make_key(key, tenant_id) for key in keys]
        
        async def _delete():
            return await self._client.delete(*full_keys)
        
        result = await self._execute_with_retry(_delete)
        return result or 0
    
    async def exists(
        self,
        *keys: str,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Check if keys exist in cache.
        
        Args:
            *keys: Cache keys to check
            tenant_id: Optional tenant identifier
            
        Returns:
            Number of keys that exist
        """
        if not keys:
            return 0
        
        full_keys = [self._make_key(key, tenant_id) for key in keys]
        
        async def _exists():
            return await self._client.exists(*full_keys)
        
        result = await self._execute_with_retry(_exists)
        return result or 0
    
    async def increment(
        self,
        key: str,
        amount: int = 1,
        tenant_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Atomic increment operation.
        
        Args:
            key: Cache key
            amount: Increment amount (can be negative)
            tenant_id: Optional tenant identifier
            
        Returns:
            New value after increment or None if failed
        """
        full_key = self._make_key(key, tenant_id)
        
        async def _incr():
            if amount == 1:
                return await self._client.incr(full_key)
            elif amount == -1:
                return await self._client.decr(full_key)
            else:
                return await self._client.incrby(full_key, amount)
        
        return await self._execute_with_retry(_incr)
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Coroutine[Any, Any, T]],
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[T]:
        """
        Cache-aside pattern implementation.
        
        Gets value from cache or calls factory function to generate
        and cache the value if not found.
        
        Args:
            key: Cache key
            factory: Async function to generate value if not cached
            ttl: Time to live in seconds
            tenant_id: Optional tenant identifier
            
        Returns:
            Cached or generated value
        """
        # Try to get from cache first
        value = await self.get(key, tenant_id)
        if value is not None:
            return value
        
        # Generate value
        try:
            value = await factory()
            if value is not None:
                await self.set(key, value, ttl, tenant_id)
            return value
        except Exception as e:
            logger.error(f"Factory function failed in get_or_set: {e}")
            return None
    
    async def clear_pattern(
        self,
        pattern: str,
        tenant_id: Optional[str] = None,
        batch_size: int = SCAN_COUNT
    ) -> int:
        """
        Delete all keys matching pattern.
        
        Uses SCAN for memory-efficient deletion of large key sets.
        
        Args:
            pattern: Key pattern (supports * and ? wildcards)
            tenant_id: Optional tenant identifier
            batch_size: Number of keys to scan per iteration
            
        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern, tenant_id)
        deleted_count = 0
        
        async def _clear():
            nonlocal deleted_count
            cursor = 0
            
            while True:
                cursor, keys = await self._client.scan(
                    cursor,
                    match=full_pattern,
                    count=batch_size
                )
                
                if keys:
                    deleted = await self._client.delete(*keys)
                    deleted_count += deleted
                
                if cursor == 0:
                    break
            
            return deleted_count
        
        await self._execute_with_retry(_clear)
        return deleted_count
    
    async def get_ttl(
        self,
        key: str,
        tenant_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Get remaining TTL for a key.
        
        Args:
            key: Cache key
            tenant_id: Optional tenant identifier
            
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist, None if error
        """
        full_key = self._make_key(key, tenant_id)
        
        async def _ttl():
            return await self._client.ttl(full_key)
        
        return await self._execute_with_retry(_ttl)
    
    async def expire(
        self,
        key: str,
        ttl: int,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Set TTL on existing key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            tenant_id: Optional tenant identifier
            
        Returns:
            True if TTL was set, False if key doesn't exist
        """
        full_key = self._make_key(key, tenant_id)
        
        async def _expire():
            return await self._client.expire(full_key, ttl)
        
        result = await self._execute_with_retry(_expire)
        return bool(result)
    
    # Pub/Sub methods for real-time messaging
    
    async def publish(
        self,
        channel: str,
        message: Union[str, Dict[str, Any]],
        tenant_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Publish message to channel.
        
        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized if dict)
            tenant_id: Optional tenant identifier
            
        Returns:
            Number of subscribers that received the message
        """
        full_channel = self._make_key(channel, tenant_id)
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        async def _publish():
            return await self._client.publish(full_channel, message)
        
        return await self._execute_with_retry(_publish)
    
    @asynccontextmanager
    async def subscribe(
        self,
        *channels: str,
        tenant_id: Optional[str] = None
    ) -> AsyncGenerator[PubSub, None]:
        """
        Subscribe to channels with context manager.
        
        Args:
            *channels: Channel names to subscribe to
            tenant_id: Optional tenant identifier
            
        Yields:
            PubSub instance for receiving messages
            
        Example:
            async with cache_manager.subscribe("updates", "notifications") as pubsub:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        print(f"Received: {message['data']}")
        """
        await self.connect()
        
        full_channels = [self._make_key(ch, tenant_id) for ch in channels]
        pubsub = self._client.pubsub()
        
        try:
            await pubsub.subscribe(*full_channels)
            yield pubsub
        finally:
            await pubsub.unsubscribe(*full_channels)
            await pubsub.close()
    
    # Distributed locking
    
    @asynccontextmanager
    async def lock(
        self,
        resource: str,
        timeout: int = LOCK_TIMEOUT,
        tenant_id: Optional[str] = None
    ) -> AsyncGenerator[bool, None]:
        """
        Distributed lock using SET NX with TTL.
        
        Args:
            resource: Resource identifier to lock
            timeout: Lock timeout in seconds
            tenant_id: Optional tenant identifier
            
        Yields:
            True if lock acquired, False otherwise
            
        Example:
            async with cache_manager.lock("user:123:update") as acquired:
                if acquired:
                    # Perform exclusive operation
                    await update_user(123)
                else:
                    # Handle lock not acquired
                    logger.warning("Could not acquire lock")
        """
        lock_key = f"{CacheKeyPrefix.LOCK}:{resource}"
        full_key = self._make_key(lock_key, tenant_id)
        lock_value = f"{id(self)}:{time.time()}"
        
        # Try to acquire lock
        acquired = await self.set(
            lock_key,
            lock_value,
            ttl=timeout,
            tenant_id=tenant_id,
            nx=True
        )
        
        try:
            yield acquired
        finally:
            if acquired:
                # Only delete if we own the lock
                current_value = await self.get(lock_key, tenant_id)
                if current_value == lock_value:
                    await self.delete(lock_key, tenant_id=tenant_id)
    
    # Rate limiting
    
    async def is_rate_limited(
        self,
        identifier: str,
        limit: int,
        window: int,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if identifier is rate limited.
        
        Uses sliding window rate limiting.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP)
            limit: Maximum requests allowed
            window: Time window in seconds
            tenant_id: Optional tenant identifier
            
        Returns:
            True if rate limited, False otherwise
        """
        key = f"{CacheKeyPrefix.RATE_LIMIT}:{identifier}"
        
        current = await self.increment(key, tenant_id=tenant_id)
        if current is None:
            return False
        
        if current == 1:
            # First request, set TTL
            await self.expire(key, window, tenant_id)
        
        return current > limit
    
    # Health check
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cache connection.
        
        Returns:
            Dictionary with health status and metrics
        """
        try:
            await self.connect()
            
            # Ping test
            start_time = time.time()
            await self._client.ping()
            ping_time = (time.time() - start_time) * 1000  # ms
            
            # Get server info
            info = await self._client.info()
            
            return {
                "status": "healthy",
                "connected": True,
                "ping_ms": round(ping_time, 2),
                "version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


# Decorator for caching function results
def cached(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[Callable[..., str]] = None
):
    """
    Decorator for caching async function results.
    
    Args:
        key_prefix: Prefix for cache keys
        ttl: Cache TTL in seconds
        key_func: Optional function to generate cache key from arguments
        
    Example:
        @cached("user", ttl=3600)
        async def get_user(user_id: int) -> User:
            return await db.get_user(user_id)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # Simple key generation from args
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"
            
            # Try cache first
            result = await cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


# Import time at module level for lock implementation
import time

# Create singleton instance
cache_manager = CacheManager()

# Export convenience functions
get = cache_manager.get
set = cache_manager.set
delete = cache_manager.delete
exists = cache_manager.exists
increment = cache_manager.increment
get_or_set = cache_manager.get_or_set
clear_pattern = cache_manager.clear_pattern
publish = cache_manager.publish
subscribe = cache_manager.subscribe
lock = cache_manager.lock
is_rate_limited = cache_manager.is_rate_limited