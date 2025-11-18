"""
Response Caching Middleware for Hot API Endpoints

Features:
- Automatic response caching for GET requests
- Configurable TTL per endpoint
- Cache invalidation on POST/PUT/DELETE
- Cache key generation from request params
- Cache hit/miss tracking
- Decorator for easy endpoint caching
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from backend.redis_cache import get_redis_cache, make_cache_key

logger = logging.getLogger(__name__)


class CacheConfig:
    """Configuration for endpoint caching."""

    def __init__(self, ttl: int = 300, key_prefix: str = "api"):
        """
        Initialize cache configuration.

        Args:
            ttl: Time-to-live in seconds (default: 5 minutes)
            key_prefix: Prefix for cache keys (default: "api")
        """
        self.ttl = ttl
        self.key_prefix = key_prefix


class ResponseCache:
    """
    Response caching for API endpoints.

    Caches GET request responses in Redis with configurable TTL.
    Automatically invalidates cache on write operations.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize response cache.

        Args:
            default_ttl: Default cache TTL in seconds (default: 5 minutes)
        """
        self.default_ttl = default_ttl
        self.cache = get_redis_cache()
        self._endpoint_config: dict[str, CacheConfig] = {}

    def configure_endpoint(
        self,
        endpoint: str,
        ttl: int,
        key_prefix: str = "api",
    ) -> None:
        """
        Configure caching for a specific endpoint.

        Args:
            endpoint: Endpoint path (e.g., "/api/v1/users")
            ttl: Cache TTL in seconds
            key_prefix: Cache key prefix
        """
        self._endpoint_config[endpoint] = CacheConfig(ttl=ttl, key_prefix=key_prefix)

    def _get_config(self, endpoint: str) -> CacheConfig:
        """Get configuration for endpoint or default."""
        return self._endpoint_config.get(
            endpoint,
            CacheConfig(ttl=self.default_ttl, key_prefix="api"),
        )

    def _make_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request.

        Args:
            request: FastAPI request

        Returns:
            Cache key string

        Key format: {prefix}:{method}:{path}:{query_hash}
        """
        config = self._get_config(request.url.path)

        # Include query parameters in key
        query_params = dict(request.query_params)
        query_str = json.dumps(query_params, sort_keys=True)
        query_hash = hashlib.sha256(query_str.encode()).hexdigest()[:8]

        # Include API key/user in cache key for personalized responses
        auth_header = request.headers.get("Authorization", "")
        user_hash = "anon"
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "", 1).strip()
            if api_key:
                user_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]

        return make_cache_key(
            config.key_prefix,
            request.method,
            request.url.path,
            user_hash,
            query_hash,
        )

    async def get_cached_response(self, request: Request) -> Optional[Response]:
        """
        Get cached response for request.

        Args:
            request: FastAPI request

        Returns:
            Cached response or None if not found
        """
        # Only cache GET requests
        if request.method != "GET":
            return None

        cache_key = self._make_cache_key(request)

        try:
            cached_data = await self.cache.get(cache_key)

            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                return JSONResponse(
                    content=cached_data["content"],
                    status_code=cached_data.get("status_code", 200),
                    headers={
                        **cached_data.get("headers", {}),
                        "X-Cache": "HIT",
                    },
                )

            logger.debug(f"Cache MISS: {cache_key}")
            return None

        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None

    async def cache_response(
        self,
        request: Request,
        response: Response,
    ) -> None:
        """
        Cache a response.

        Args:
            request: FastAPI request
            response: FastAPI response
        """
        # Only cache successful GET responses
        if request.method != "GET" or response.status_code >= 400:
            return

        cache_key = self._make_cache_key(request)
        config = self._get_config(request.url.path)

        try:
            # Extract response body
            if isinstance(response, JSONResponse):
                # For JSONResponse, get the content directly
                import json

                content = json.loads(response.body.decode())
            else:
                # For other responses, try to parse as JSON
                try:
                    content = json.loads(response.body.decode())
                except (json.JSONDecodeError, AttributeError):
                    # Can't cache non-JSON responses
                    logger.debug(f"Skipping cache for non-JSON response: {cache_key}")
                    return

            # Cache the response
            cache_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

            await self.cache.set(cache_key, cache_data, ttl=config.ttl)
            logger.debug(f"Cached response: {cache_key} (TTL: {config.ttl}s)")

        except Exception as e:
            logger.error(f"Error caching response: {e}")

    async def invalidate_endpoint(self, endpoint: str) -> int:
        """
        Invalidate all cached responses for an endpoint.

        Args:
            endpoint: Endpoint path

        Returns:
            Number of cache entries deleted
        """
        config = self._get_config(endpoint)
        pattern = f"{config.key_prefix}:*:{endpoint}:*"

        try:
            deleted = await self.cache.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted} cache entries for {endpoint}")
            return deleted
        except Exception as e:
            logger.error(f"Error invalidating cache for {endpoint}: {e}")
            return 0

    async def invalidate_all(self) -> int:
        """
        Invalidate all API cache entries.

        Returns:
            Number of cache entries deleted
        """
        try:
            deleted = await self.cache.delete_pattern("api:*")
            logger.info(f"Invalidated {deleted} API cache entries")
            return deleted
        except Exception as e:
            logger.error(f"Error invalidating all cache: {e}")
            return 0


# ============================================================================
# FastAPI Middleware
# ============================================================================


class CacheMiddleware:
    """
    FastAPI middleware for automatic response caching.

    Caches GET responses and invalidates on write operations.
    """

    def __init__(
        self,
        app,
        default_ttl: int = 300,
        cache_endpoints: Optional[dict[str, int]] = None,
    ):
        """
        Initialize cache middleware.

        Args:
            app: FastAPI application
            default_ttl: Default cache TTL in seconds
            cache_endpoints: Dict of endpoint paths to TTL values
        """
        self.app = app
        self.cache_manager = ResponseCache(default_ttl=default_ttl)

        # Configure specific endpoints
        if cache_endpoints:
            for endpoint, ttl in cache_endpoints.items():
                self.cache_manager.configure_endpoint(endpoint, ttl)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with caching.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response (cached or fresh)
        """
        # Skip caching for certain paths
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Try to get cached response for GET requests
        if request.method == "GET":
            cached_response = await self.cache_manager.get_cached_response(request)
            if cached_response:
                return cached_response

        # Process request
        response = await call_next(request)

        # Cache GET responses
        if request.method == "GET":
            await self.cache_manager.cache_response(request, response)
            response.headers["X-Cache"] = "MISS"

        # Invalidate cache for write operations
        elif request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            await self.cache_manager.invalidate_endpoint(request.url.path)
            response.headers["X-Cache"] = "INVALIDATED"

        return response


# ============================================================================
# Decorator for Endpoint Caching
# ============================================================================


def cached(ttl: int = 300, key_prefix: str = "api"):
    """
    Decorator for caching endpoint responses.

    Usage:
        @app.get("/api/users")
        @cached(ttl=600)
        async def get_users():
            return {"users": [...]}

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Cache key prefix

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs (injected by FastAPI)
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # No request found, can't cache
                return await func(*args, **kwargs)

            cache = get_redis_cache()

            # Generate cache key
            query_str = json.dumps(dict(request.query_params), sort_keys=True)
            query_hash = hashlib.sha256(query_str.encode()).hexdigest()[:8]
            cache_key = make_cache_key(
                key_prefix,
                request.method,
                request.url.path,
                query_hash,
            )

            # Try to get cached response
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT (decorator): {cache_key}")
                return cached_data

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cached result (decorator): {cache_key} (TTL: {ttl}s)")

            return result

        return wrapper

    return decorator


# ============================================================================
# Global Cache Manager Instance
# ============================================================================

_global_cache_manager: Optional[ResponseCache] = None


def get_cache_manager(default_ttl: int = 300) -> ResponseCache:
    """
    Get global cache manager instance.

    Args:
        default_ttl: Default cache TTL in seconds

    Returns:
        ResponseCache instance
    """
    global _global_cache_manager

    if _global_cache_manager is None:
        _global_cache_manager = ResponseCache(default_ttl=default_ttl)

    return _global_cache_manager


# ============================================================================
# Hot Endpoints Configuration
# ============================================================================

# Configure caching for hot endpoints
HOT_ENDPOINTS = {
    "/api/health": 60,  # 1 minute
    "/api/scrape": 300,  # 5 minutes (scraping results)
    "/api/query": 600,  # 10 minutes (query results)
    "/api/analyze": 1800,  # 30 minutes (analysis results)
    "/api/api-keys": 120,  # 2 minutes (API key list)
    "/api/tokens/balance": 60,  # 1 minute (token balance)
    "/api/attributions": 300,  # 5 minutes (attributions list)
}


def configure_hot_endpoints(cache_manager: ResponseCache) -> None:
    """
    Configure caching for hot endpoints.

    Args:
        cache_manager: ResponseCache instance
    """
    for endpoint, ttl in HOT_ENDPOINTS.items():
        cache_manager.configure_endpoint(endpoint, ttl)
        logger.info(f"Configured caching for {endpoint} (TTL: {ttl}s)")
