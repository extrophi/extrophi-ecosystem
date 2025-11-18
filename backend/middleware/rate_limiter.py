"""
Redis-Backed Rate Limiting Middleware

Extends RHO #55 API key authentication with Redis-based rate limiting.

Features:
- Per-API-key rate limiting using Redis
- Sliding window algorithm for accurate limits
- Distributed rate limiting (works across multiple instances)
- Configurable limits per endpoint
- Rate limit headers (X-RateLimit-*)
- Automatic cleanup of expired windows
"""

import logging
import time
from typing import Callable, Optional

from fastapi import Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from backend.redis_cache import get_redis_cache, make_cache_key

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm.

    Supports:
    - Per-API-key limits
    - Per-endpoint limits
    - Global limits
    - Custom time windows (second, minute, hour, day)
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute (default: 60)
            requests_per_hour: Max requests per hour (default: 1000)
            requests_per_day: Max requests per day (default: 10000)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.cache = get_redis_cache()

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (API key hash, user_id, IP)
            endpoint: Optional endpoint path for per-endpoint limits

        Returns:
            Tuple of (is_allowed, rate_limit_info)

        Rate limit info contains:
        - limit: Max requests allowed
        - remaining: Requests remaining in window
        - reset: Unix timestamp when window resets
        - retry_after: Seconds to wait before retry (if blocked)
        """
        now = int(time.time())

        # Check minute window
        minute_key = make_cache_key("ratelimit", "minute", identifier, endpoint or "global")
        minute_allowed, minute_info = await self._check_window(
            minute_key, now, 60, self.requests_per_minute
        )

        # Check hour window
        hour_key = make_cache_key("ratelimit", "hour", identifier, endpoint or "global")
        hour_allowed, hour_info = await self._check_window(
            hour_key, now, 3600, self.requests_per_hour
        )

        # Check day window
        day_key = make_cache_key("ratelimit", "day", identifier, endpoint or "global")
        day_allowed, day_info = await self._check_window(
            day_key, now, 86400, self.requests_per_day
        )

        # Request is allowed only if all windows allow it
        is_allowed = minute_allowed and hour_allowed and day_allowed

        # Use the most restrictive window for rate limit info
        if not minute_allowed:
            info = minute_info
        elif not hour_allowed:
            info = hour_info
        elif not day_allowed:
            info = day_info
        else:
            # Use minute window info if all allowed
            info = minute_info

        return is_allowed, info

    async def _check_window(
        self,
        key: str,
        now: int,
        window_seconds: int,
        max_requests: int,
    ) -> tuple[bool, dict]:
        """
        Check rate limit for a specific time window using sliding window.

        Args:
            key: Redis key for this window
            now: Current timestamp
            window_seconds: Window size in seconds
            max_requests: Maximum requests in window

        Returns:
            Tuple of (is_allowed, window_info)
        """
        window_start = now - window_seconds

        try:
            # Remove old requests outside the window
            # Using sorted set with timestamps as scores
            await self.cache._redis.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            current_count = await self.cache._redis.zcard(key)

            # Calculate info
            window_reset = now + window_seconds
            remaining = max(0, max_requests - current_count)
            retry_after = window_seconds if current_count >= max_requests else 0

            info = {
                "limit": max_requests,
                "remaining": remaining,
                "reset": window_reset,
                "retry_after": retry_after,
            }

            # Check if limit exceeded
            if current_count >= max_requests:
                return False, info

            # Add current request to window
            await self.cache._redis.zadd(key, {str(now): now})

            # Set expiration on key (cleanup old windows)
            await self.cache._redis.expire(key, window_seconds * 2)

            return True, info

        except Exception as e:
            logger.error(f"Error checking rate limit for key '{key}': {e}")
            # On error, allow the request (fail open)
            return True, {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": now + window_seconds,
                "retry_after": 0,
            }

    async def record_request(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
    ) -> None:
        """
        Record a request in the rate limit windows.

        Args:
            identifier: Unique identifier (API key, user_id, IP)
            endpoint: Optional endpoint path
        """
        now = int(time.time())

        # Record in all windows
        minute_key = make_cache_key("ratelimit", "minute", identifier, endpoint or "global")
        hour_key = make_cache_key("ratelimit", "hour", identifier, endpoint or "global")
        day_key = make_cache_key("ratelimit", "day", identifier, endpoint or "global")

        try:
            # Add to sorted sets
            await self.cache._redis.zadd(minute_key, {str(now): now})
            await self.cache._redis.zadd(hour_key, {str(now): now})
            await self.cache._redis.zadd(day_key, {str(now): now})

            # Set expirations
            await self.cache._redis.expire(minute_key, 120)  # 2 minutes
            await self.cache._redis.expire(hour_key, 7200)  # 2 hours
            await self.cache._redis.expire(day_key, 172800)  # 2 days

        except Exception as e:
            logger.error(f"Error recording request for '{identifier}': {e}")

    async def reset_limit(self, identifier: str, endpoint: Optional[str] = None) -> None:
        """
        Reset rate limit for an identifier.

        Args:
            identifier: Unique identifier
            endpoint: Optional endpoint path
        """
        minute_key = make_cache_key("ratelimit", "minute", identifier, endpoint or "global")
        hour_key = make_cache_key("ratelimit", "hour", identifier, endpoint or "global")
        day_key = make_cache_key("ratelimit", "day", identifier, endpoint or "global")

        try:
            await self.cache.delete(minute_key)
            await self.cache.delete(hour_key)
            await self.cache.delete(day_key)
            logger.info(f"Reset rate limit for '{identifier}'")
        except Exception as e:
            logger.error(f"Error resetting rate limit for '{identifier}': {e}")

    async def get_stats(self, identifier: str) -> dict:
        """
        Get rate limit statistics for an identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with rate limit stats
        """
        now = int(time.time())

        try:
            # Get counts for each window
            minute_key = make_cache_key("ratelimit", "minute", identifier, "global")
            hour_key = make_cache_key("ratelimit", "hour", identifier, "global")
            day_key = make_cache_key("ratelimit", "day", identifier, "global")

            minute_count = await self.cache._redis.zcard(minute_key)
            hour_count = await self.cache._redis.zcard(hour_key)
            day_count = await self.cache._redis.zcard(day_key)

            return {
                "identifier": identifier,
                "minute": {
                    "count": minute_count,
                    "limit": self.requests_per_minute,
                    "remaining": max(0, self.requests_per_minute - minute_count),
                },
                "hour": {
                    "count": hour_count,
                    "limit": self.requests_per_hour,
                    "remaining": max(0, self.requests_per_hour - hour_count),
                },
                "day": {
                    "count": day_count,
                    "limit": self.requests_per_day,
                    "remaining": max(0, self.requests_per_day - day_count),
                },
            }
        except Exception as e:
            logger.error(f"Error getting stats for '{identifier}': {e}")
            return {
                "identifier": identifier,
                "error": str(e),
            }


# ============================================================================
# FastAPI Middleware
# ============================================================================


class RateLimitMiddleware:
    """
    FastAPI middleware for automatic rate limiting.

    Extracts API key from Authorization header and enforces rate limits.
    Adds rate limit headers to responses.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            requests_per_day: Max requests per day
        """
        self.app = app
        self.limiter = RedisRateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day,
        )

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and enforce rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Extract identifier (API key or IP address)
        identifier = self._get_identifier(request)
        endpoint = request.url.path

        # Check rate limit
        is_allowed, rate_info = await self.limiter.check_rate_limit(identifier, endpoint)

        # Rate limit exceeded
        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {rate_info['retry_after']} seconds.",
                    "retry_after": rate_info["retry_after"],
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["retry_after"]),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        return response

    def _get_identifier(self, request: Request) -> str:
        """
        Extract identifier from request (API key or IP).

        Args:
            request: FastAPI request

        Returns:
            Unique identifier string
        """
        # Try to get API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "", 1).strip()
            if api_key:
                # Use hash of API key as identifier
                import hashlib

                return hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


# ============================================================================
# Global Rate Limiter Instance
# ============================================================================

_global_limiter: Optional[RedisRateLimiter] = None


def get_rate_limiter(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    requests_per_day: int = 10000,
) -> RedisRateLimiter:
    """
    Get global rate limiter instance.

    Args:
        requests_per_minute: Max requests per minute
        requests_per_hour: Max requests per hour
        requests_per_day: Max requests per day

    Returns:
        RedisRateLimiter instance
    """
    global _global_limiter

    if _global_limiter is None:
        _global_limiter = RedisRateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day,
        )

    return _global_limiter
