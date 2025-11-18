"""API response caching middleware for improved performance.

This middleware caches GET requests to reduce database load and improve response times.
"""

import hashlib
import json
import time
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class CacheEntry:
    """Cache entry with expiration and metadata."""

    def __init__(
        self,
        content: Any,
        status_code: int,
        headers: dict,
        ttl: int,
        content_type: str = "application/json"
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers
        self.content_type = content_type
        self.expires_at = time.time() + ttl
        self.created_at = time.time()
        self.hit_count = 0

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def get_age(self) -> int:
        """Get age of cache entry in seconds."""
        return int(time.time() - self.created_at)


class APICacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching API responses.

    Features:
    - Caches GET requests only
    - Path-based and query-param-aware cache keys
    - TTL-based expiration
    - Automatic cleanup of expired entries
    - Cache statistics
    - Configurable exclusions
    """

    def __init__(
        self,
        app,
        default_ttl: int = 300,
        max_cache_size: int = 1000,
        exclude_paths: Optional[list[str]] = None,
        cache_query_params: bool = True
    ):
        """
        Initialize cache middleware.

        Args:
            app: FastAPI application
            default_ttl: Default cache TTL in seconds (5 minutes)
            max_cache_size: Maximum number of cache entries
            exclude_paths: List of path patterns to exclude from caching
            cache_query_params: Include query params in cache key
        """
        super().__init__(app)
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        self.cache_query_params = cache_query_params
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "stores": 0
        }

        # Path-specific TTL configurations (in seconds)
        self.path_ttl: dict[str, int] = {
            "/query/rag": 60,  # 1 minute for RAG queries
            "/scrape": 300,  # 5 minutes for scrape results
            "/api/cards": 120,  # 2 minutes for card listings
            "/api/users": 180,  # 3 minutes for user data
            "/api/attributions": 120,  # 2 minutes for attributions
            "/api/tokens": 60,  # 1 minute for token balances
        }

    def _make_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request.

        Args:
            request: FastAPI request

        Returns:
            SHA256-based cache key
        """
        key_parts = [
            request.url.path,
        ]

        if self.cache_query_params and request.url.query:
            # Sort query params for consistent keys
            sorted_params = sorted(request.query_params.items())
            key_parts.append(str(sorted_params))

        # Include auth header for user-specific caching
        auth_header = request.headers.get("authorization", "")
        if auth_header:
            key_parts.append(auth_header[:50])  # Truncate for privacy

        key_str = "|".join(key_parts)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()

        return f"api:{key_hash}"

    def _should_cache(self, request: Request) -> bool:
        """
        Determine if request should be cached.

        Args:
            request: FastAPI request

        Returns:
            True if request should be cached
        """
        # Only cache GET requests
        if request.method != "GET":
            return False

        # Check excluded paths
        path = request.url.path
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                return False

        # Don't cache requests with cache control headers
        cache_control = request.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False

        return True

    def _get_ttl(self, path: str) -> int:
        """
        Get TTL for specific path.

        Args:
            path: Request path

        Returns:
            TTL in seconds
        """
        for pattern, ttl in self.path_ttl.items():
            if path.startswith(pattern):
                return ttl

        return self.default_ttl

    def _evict_oldest(self) -> None:
        """Evict oldest cache entry if cache is full."""
        if len(self._cache) >= self.max_cache_size:
            # Find oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]
            self._stats["evictions"] += 1

    def _cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with caching.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Cached or fresh response
        """
        # Check if request should be cached
        if not self._should_cache(request):
            return await call_next(request)

        # Generate cache key
        cache_key = self._make_cache_key(request)

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]

            if not entry.is_expired():
                # Cache hit
                self._stats["hits"] += 1
                entry.hit_count += 1

                # Return cached response with age header
                response = JSONResponse(
                    content=entry.content,
                    status_code=entry.status_code,
                    headers={
                        **entry.headers,
                        "X-Cache": "HIT",
                        "X-Cache-Age": str(entry.get_age()),
                    }
                )
                return response
            else:
                # Expired entry, remove it
                del self._cache[cache_key]

        # Cache miss - call endpoint
        self._stats["misses"] += 1

        response = await call_next(request)

        # Only cache successful responses
        if response.status_code == 200:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            try:
                content = json.loads(body.decode())

                # Store in cache
                ttl = self._get_ttl(request.url.path)

                # Evict if cache is full
                self._evict_oldest()

                self._cache[cache_key] = CacheEntry(
                    content=content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    ttl=ttl
                )
                self._stats["stores"] += 1

                # Return response with cache headers
                return JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "X-Cache": "MISS",
                        "Cache-Control": f"max-age={ttl}",
                    }
                )

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Non-JSON response, return as-is
                pass

        return response

    def invalidate(self, path_pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            path_pattern: Optional pattern to match paths (invalidates all if None)

        Returns:
            Number of entries invalidated
        """
        if path_pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        # Invalidate matching entries
        # Note: This requires storing path in cache entry (TODO: enhancement)
        return 0

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())

        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "stores": self._stats["stores"],
            "evictions": self._stats["evictions"],
            "hit_rate": round(hit_rate, 2),
            "max_cache_size": self.max_cache_size,
            "memory_usage_estimate_mb": round(
                sum(
                    len(str(entry.content))
                    for entry in self._cache.values()
                ) / (1024 * 1024),
                2
            )
        }


# Global cache instance for stats access
_cache_middleware: Optional[APICacheMiddleware] = None


def setup_cache_middleware(app, **kwargs):
    """
    Setup cache middleware on FastAPI app.

    Args:
        app: FastAPI application
        **kwargs: Arguments passed to APICacheMiddleware
    """
    global _cache_middleware
    _cache_middleware = APICacheMiddleware(app, **kwargs)
    app.add_middleware(APICacheMiddleware, **kwargs)
    return _cache_middleware


def get_cache_stats() -> dict:
    """
    Get cache statistics from global middleware instance.

    Returns:
        Cache statistics or empty dict if middleware not setup
    """
    if _cache_middleware:
        return _cache_middleware.get_stats()
    return {}
