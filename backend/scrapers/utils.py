"""Scraper utilities for rate limiting, caching, and retry logic."""

import asyncio
import functools
import hashlib
import json
import logging
import time
from typing import Any, Callable, TypeVar

import redis

logger = logging.getLogger(__name__)

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, calls: int, period: float) -> None:
        """
        Initialize rate limiter.

        Args:
            calls: Maximum number of calls allowed
            period: Time period in seconds for the calls limit
        """
        self.calls = calls
        self.period = period
        self.tokens = calls
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(self.calls, self.tokens + (elapsed * self.calls / self.period))
            self.last_update = now

            if self.tokens < 1:
                # Wait until next token is available
                wait_time = (1 - self.tokens) * self.period / self.calls
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 1

            self.tokens -= 1


class ScraperCache:
    """Redis-based cache for scraper results."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl: int = 3600) -> None:
        """
        Initialize cache.

        Args:
            redis_url: Redis connection URL
            ttl: Time to live in seconds (default 1 hour)
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.ttl = ttl
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis cache disabled: {e}")
            self.enabled = False

    def _make_key(self, platform: str, target: str, params: dict[str, Any]) -> str:
        """Generate cache key from parameters."""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"scraper:{platform}:{target}:{params_hash}"

    async def get(self, platform: str, target: str, **params: Any) -> list[dict] | None:
        """
        Retrieve cached scraper results.

        Args:
            platform: Platform name (twitter, youtube, etc.)
            target: Target identifier (username, video_id, etc.)
            **params: Additional parameters used in the scrape

        Returns:
            Cached results or None if not found/expired
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key(platform, target, params)
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"Cache hit: {key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    async def set(self, platform: str, target: str, results: list[dict], **params: Any) -> None:
        """
        Store scraper results in cache.

        Args:
            platform: Platform name
            target: Target identifier
            results: Results to cache
            **params: Additional parameters used in the scrape
        """
        if not self.enabled or not results:
            return

        try:
            key = self._make_key(platform, target, params)
            self.redis_client.setex(key, self.ttl, json.dumps(results))
            logger.debug(f"Cache set: {key} (ttl={self.ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def invalidate(self, platform: str, target: str, **params: Any) -> None:
        """Invalidate cache for specific target."""
        if not self.enabled:
            return

        try:
            key = self._make_key(platform, target, params)
            self.redis_client.delete(key)
            logger.debug(f"Cache invalidated: {key}")
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")


def rate_limit(calls: int = 10, period: float = 60.0) -> Callable[[F], F]:
    """
    Decorator to rate limit function calls.

    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds

    Example:
        @rate_limit(calls=10, period=60)
        async def scrape_twitter(username: str):
            # Limited to 10 calls per 60 seconds
            ...
    """
    limiter = RateLimiter(calls, period)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            await limiter.acquire()
            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
) -> Callable[[F], F]:
    """
    Decorator to retry failed async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def fetch_data():
            # Will retry up to 3 times with exponential backoff
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)

            raise last_exception  # Should never reach here, but satisfies type checker

        return wrapper  # type: ignore

    return decorator


def cached(cache: ScraperCache, platform: str) -> Callable[[F], F]:
    """
    Decorator to cache scraper results.

    Args:
        cache: ScraperCache instance
        platform: Platform name for cache key

    Example:
        cache = ScraperCache()

        @cached(cache, "twitter")
        async def extract_tweets(target: str, limit: int):
            # Results will be cached
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract target from arguments
            target = args[1] if len(args) > 1 else kwargs.get("target", "unknown")

            # Try to get from cache
            cached_result = await cache.get(platform, str(target), **kwargs)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result:
                await cache.set(platform, str(target), result, **kwargs)

            return result

        return wrapper  # type: ignore

    return decorator
