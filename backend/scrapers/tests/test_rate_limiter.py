"""Tests for rate limiting functionality."""

import asyncio

import pytest

from backend.scrapers.rate_limiter import (
    RateLimitConfig,
    RateLimitExceeded,
    RateLimiter,
)


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_rate_limit_config_defaults(self):
        """Test default rate limit configuration."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_size == 10

    def test_rate_limit_config_custom(self):
        """Test custom rate limit configuration."""
        config = RateLimitConfig(
            requests_per_minute=30, requests_per_hour=500, burst_size=5
        )
        assert config.requests_per_minute == 30
        assert config.requests_per_hour == 500
        assert config.burst_size == 5

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test successful token acquisition."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=60, requests_per_hour=100, burst_size=10)
        )

        # Should succeed - within burst size
        result = await limiter.acquire("test_platform", cost=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_exceeds_burst(self):
        """Test rate limit exceeded when burst depleted."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=60, requests_per_hour=100, burst_size=3)
        )

        # Consume all burst tokens
        await limiter.acquire("test_platform", cost=1)
        await limiter.acquire("test_platform", cost=1)
        await limiter.acquire("test_platform", cost=1)

        # Should raise exception
        with pytest.raises(RateLimitExceeded):
            await limiter.acquire("test_platform", cost=1)

    @pytest.mark.asyncio
    async def test_acquire_hourly_limit(self):
        """Test hourly rate limit enforcement."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=1000, requests_per_hour=5, burst_size=10)
        )

        # Make 5 requests (hourly limit)
        for _ in range(5):
            await limiter.acquire("test_platform", cost=1)

        # 6th request should fail
        with pytest.raises(RateLimitExceeded) as exc_info:
            await limiter.acquire("test_platform", cost=1)

        assert "Hourly limit reached" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self):
        """Test that tokens refill based on time elapsed."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=60, requests_per_hour=100, burst_size=2)
        )

        # Consume all tokens
        await limiter.acquire("test_platform", cost=1)
        await limiter.acquire("test_platform", cost=1)

        # Wait for refill (60 req/min = 1 req/sec)
        await asyncio.sleep(1.1)

        # Should succeed after refill
        result = await limiter.acquire("test_platform", cost=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_platform_isolation(self):
        """Test that different platforms have separate rate limits."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=60, requests_per_hour=100, burst_size=2)
        )

        # Consume all tokens for platform A
        await limiter.acquire("platform_a", cost=1)
        await limiter.acquire("platform_a", cost=1)

        # Platform B should still have tokens
        result = await limiter.acquire("platform_b", cost=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_if_needed(self):
        """Test wait_if_needed blocks until tokens available."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=120, requests_per_hour=100, burst_size=2)
        )

        # Consume all tokens
        await limiter.acquire("test_platform", cost=1)
        await limiter.acquire("test_platform", cost=1)

        # Should wait ~0.5s for refill (120 req/min = 2 req/sec)
        start = asyncio.get_event_loop().time()
        await limiter.wait_if_needed("test_platform", cost=1)
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed >= 0.4  # Allow some margin

    def test_get_stats(self):
        """Test rate limiter statistics."""
        limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=60, requests_per_hour=100, burst_size=10)
        )

        stats = limiter.get_stats("test_platform")

        assert stats["platform"] == "test_platform"
        assert stats["max_tokens"] == 10
        assert stats["hourly_limit"] == 100
        assert stats["requests_per_minute"] == 60
        # Allow floating point precision errors
        assert abs(stats["tokens_available"] - 10) < 0.01
        assert stats["requests_last_hour"] == 0
