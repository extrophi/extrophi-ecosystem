"""Cache module for Redis-backed caching."""

from backend.redis_cache import (
    RedisCache,
    close_redis_cache,
    get_redis_cache,
    init_redis_cache,
    make_cache_key,
)

__all__ = [
    "RedisCache",
    "get_redis_cache",
    "init_redis_cache",
    "close_redis_cache",
    "make_cache_key",
]
