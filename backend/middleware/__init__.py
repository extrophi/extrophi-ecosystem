"""Middleware module for rate limiting and caching."""

from backend.middleware.caching import (
    CacheMiddleware,
    cached,
    configure_hot_endpoints,
    get_cache_manager,
)
from backend.middleware.rate_limiter import (
    RateLimitMiddleware,
    RedisRateLimiter,
    get_rate_limiter,
)

__all__ = [
    "RateLimitMiddleware",
    "RedisRateLimiter",
    "get_rate_limiter",
    "CacheMiddleware",
    "cached",
    "get_cache_manager",
    "configure_hot_endpoints",
]
