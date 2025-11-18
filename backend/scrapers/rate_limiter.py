"""Rate limiting for scrapers to prevent API abuse and rate limit violations."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.

    Features:
    - Per-platform rate limiting
    - Burst allowance for sudden spikes
    - Automatic token regeneration
    - Thread-safe with asyncio locks
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if not provided)
        """
        self.config = config or RateLimitConfig()

        # Per-platform token buckets
        self._tokens: dict[str, float] = defaultdict(lambda: self.config.burst_size)
        self._last_refill: dict[str, float] = defaultdict(time.time)

        # Track request history for hourly limits
        self._request_times: dict[str, list[float]] = defaultdict(list)

        # Locks for thread safety
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire(self, platform: str, cost: int = 1) -> bool:
        """
        Acquire tokens for a request.

        Args:
            platform: Platform identifier (twitter, youtube, reddit, web)
            cost: Number of tokens required (default 1)

        Returns:
            True if request allowed, raises exception if rate limited

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        async with self._locks[platform]:
            # Refill tokens based on time elapsed
            self._refill_tokens(platform)

            # Check hourly limit
            self._clean_old_requests(platform)
            if len(self._request_times[platform]) >= self.config.requests_per_hour:
                wait_time = 3600 - (time.time() - self._request_times[platform][0])
                raise RateLimitExceeded(
                    f"Hourly limit reached for {platform}. Retry in {wait_time:.0f}s"
                )

            # Check if enough tokens available
            if self._tokens[platform] < cost:
                wait_time = self._time_until_refill(platform, cost)
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {platform}. Retry in {wait_time:.1f}s"
                )

            # Consume tokens
            self._tokens[platform] -= cost
            self._request_times[platform].append(time.time())

            return True

    def _refill_tokens(self, platform: str) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill[platform]

        # Refill rate: requests_per_minute / 60 seconds
        refill_rate = self.config.requests_per_minute / 60.0
        tokens_to_add = elapsed * refill_rate

        self._tokens[platform] = min(
            self._tokens[platform] + tokens_to_add, self.config.burst_size
        )
        self._last_refill[platform] = now

    def _clean_old_requests(self, platform: str) -> None:
        """Remove request timestamps older than 1 hour."""
        cutoff = time.time() - 3600
        self._request_times[platform] = [
            t for t in self._request_times[platform] if t > cutoff
        ]

    def _time_until_refill(self, platform: str, required_tokens: int) -> float:
        """Calculate time until enough tokens available."""
        tokens_needed = required_tokens - self._tokens[platform]
        refill_rate = self.config.requests_per_minute / 60.0
        return tokens_needed / refill_rate

    async def wait_if_needed(self, platform: str, cost: int = 1) -> None:
        """
        Wait if rate limited, then acquire tokens.

        Args:
            platform: Platform identifier
            cost: Number of tokens required
        """
        while True:
            try:
                await self.acquire(platform, cost)
                return
            except RateLimitExceeded as e:
                wait_time = float(str(e).split("Retry in ")[1].rstrip("s"))
                await asyncio.sleep(wait_time)

    def get_stats(self, platform: str) -> dict:
        """
        Get current rate limit statistics.

        Args:
            platform: Platform identifier

        Returns:
            Statistics dict with tokens, requests, etc.
        """
        self._refill_tokens(platform)
        self._clean_old_requests(platform)

        return {
            "platform": platform,
            "tokens_available": self._tokens[platform],
            "max_tokens": self.config.burst_size,
            "requests_last_hour": len(self._request_times[platform]),
            "hourly_limit": self.config.requests_per_hour,
            "requests_per_minute": self.config.requests_per_minute,
        }


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    pass


# Global rate limiter instance with platform-specific configs
_GLOBAL_LIMITER: Optional[RateLimiter] = None


def get_rate_limiter(
    platform_configs: Optional[dict[str, RateLimitConfig]] = None
) -> RateLimiter:
    """
    Get global rate limiter instance.

    Args:
        platform_configs: Optional platform-specific configurations

    Returns:
        RateLimiter instance
    """
    global _GLOBAL_LIMITER

    if _GLOBAL_LIMITER is None:
        # Default config if none provided
        _GLOBAL_LIMITER = RateLimiter()

    return _GLOBAL_LIMITER


# Platform-specific rate limit configurations
PLATFORM_RATE_LIMITS = {
    "twitter": RateLimitConfig(
        requests_per_minute=30,  # Conservative for scraping
        requests_per_hour=900,
        burst_size=5,
    ),
    "youtube": RateLimitConfig(
        requests_per_minute=60,  # youtube-transcript-api is generous
        requests_per_hour=3000,
        burst_size=10,
    ),
    "reddit": RateLimitConfig(
        requests_per_minute=60,  # PRAW handles this internally
        requests_per_hour=1000,  # 1000 req/10min = 6000/hr, but be conservative
        burst_size=10,
    ),
    "web": RateLimitConfig(
        requests_per_minute=100,  # Jina.ai is generous (50K/month)
        requests_per_hour=5000,
        burst_size=20,
    ),
}
