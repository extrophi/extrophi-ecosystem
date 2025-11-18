"""
Tests for Redis-backed Rate Limiting and Caching (ALPHA-2)

Tests:
- Redis cache operations (get, set, delete, patterns)
- Rate limiting with sliding window algorithm
- Cache invalidation strategies
- Middleware integration
"""

import asyncio
import hashlib
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.redis_cache import RedisCache, make_cache_key
from backend.middleware.caching import CacheMiddleware, ResponseCache, cached
from backend.middleware.rate_limiter import RedisRateLimiter


class TestRedisCache:
    """Test Redis cache client."""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = RedisCache()
        await cache.connect()

        # Set a value
        key = "test:key:1"
        value = {"message": "Hello, Redis!"}
        result = await cache.set(key, value, ttl=60)
        assert result is True

        # Get the value
        retrieved = await cache.get(key)
        assert retrieved == value

        # Cleanup
        await cache.delete(key)
        await cache.disconnect()

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache TTL expiration."""
        cache = RedisCache()
        await cache.connect()

        # Set a value with 1 second TTL
        key = "test:expiring:key"
        value = {"expires": "soon"}
        await cache.set(key, value, ttl=1)

        # Should exist immediately
        assert await cache.exists(key) is True

        # Wait for expiration
        await asyncio.sleep(2)

        # Should be gone
        assert await cache.exists(key) is False

        await cache.disconnect()

    @pytest.mark.asyncio
    async def test_cache_pattern_delete(self):
        """Test pattern-based cache deletion."""
        cache = RedisCache()
        await cache.connect()

        # Set multiple keys
        await cache.set("user:1:profile", {"name": "Alice"})
        await cache.set("user:1:settings", {"theme": "dark"})
        await cache.set("user:2:profile", {"name": "Bob"})
        await cache.set("post:1:content", {"title": "Test"})

        # Delete all user:1 keys
        deleted = await cache.delete_pattern("user:1:*")
        assert deleted == 2

        # Verify deletion
        assert await cache.exists("user:1:profile") is False
        assert await cache.exists("user:1:settings") is False
        assert await cache.exists("user:2:profile") is True
        assert await cache.exists("post:1:content") is True

        # Cleanup
        await cache.clear()
        await cache.disconnect()

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        cache = RedisCache()
        await cache.connect()

        # Add some data
        await cache.set("stat:test:1", {"value": 1})
        await cache.set("stat:test:2", {"value": 2})

        # Get stats
        stats = await cache.get_stats()
        assert stats["connected"] is True
        assert "keys" in stats
        assert stats["keys"] >= 2

        # Cleanup
        await cache.delete_pattern("stat:test:*")
        await cache.disconnect()


class TestRedisRateLimiter:
    """Test Redis-backed rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limit_basic(self):
        """Test basic rate limiting."""
        limiter = RedisRateLimiter(
            requests_per_minute=5,
            requests_per_hour=10,
            requests_per_day=20,
        )

        identifier = "test_user_1"

        # First 5 requests should succeed
        for i in range(5):
            is_allowed, info = await limiter.check_rate_limit(identifier)
            assert is_allowed is True
            assert info["remaining"] >= 0

        # 6th request should be rate limited
        is_allowed, info = await limiter.check_rate_limit(identifier)
        assert is_allowed is False
        assert info["remaining"] == 0
        assert info["retry_after"] > 0

        # Reset and verify
        await limiter.reset_limit(identifier)
        is_allowed, info = await limiter.check_rate_limit(identifier)
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_per_endpoint(self):
        """Test rate limiting per endpoint."""
        limiter = RedisRateLimiter(requests_per_minute=3)

        user = "test_user_2"
        endpoint1 = "/api/users"
        endpoint2 = "/api/posts"

        # Use up limit for endpoint1
        for _ in range(3):
            is_allowed, _ = await limiter.check_rate_limit(user, endpoint1)
            assert is_allowed is True

        # endpoint1 should be limited
        is_allowed, _ = await limiter.check_rate_limit(user, endpoint1)
        assert is_allowed is False

        # endpoint2 should still work
        is_allowed, _ = await limiter.check_rate_limit(user, endpoint2)
        assert is_allowed is True

        # Cleanup
        await limiter.reset_limit(user, endpoint1)
        await limiter.reset_limit(user, endpoint2)

    @pytest.mark.asyncio
    async def test_rate_limit_stats(self):
        """Test rate limit statistics."""
        limiter = RedisRateLimiter(requests_per_minute=10)
        identifier = "test_user_3"

        # Make some requests
        for _ in range(3):
            await limiter.check_rate_limit(identifier)

        # Get stats
        stats = await limiter.get_stats(identifier)
        assert stats["identifier"] == identifier
        assert stats["minute"]["count"] == 3
        assert stats["minute"]["remaining"] == 7

        # Cleanup
        await limiter.reset_limit(identifier)


class TestResponseCache:
    """Test response caching."""

    @pytest.mark.asyncio
    async def test_cache_configuration(self):
        """Test cache endpoint configuration."""
        cache_mgr = ResponseCache(default_ttl=300)

        # Configure endpoint
        cache_mgr.configure_endpoint("/api/users", ttl=600, key_prefix="users")

        # Verify configuration
        config = cache_mgr._get_config("/api/users")
        assert config.ttl == 600
        assert config.key_prefix == "users"

        # Unknown endpoint should get defaults
        config = cache_mgr._get_config("/api/unknown")
        assert config.ttl == 300
        assert config.key_prefix == "api"

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache invalidation strategies."""
        cache_mgr = ResponseCache()
        cache = cache_mgr.cache

        await cache.connect()

        # Set some cached data
        await cache.set("api:GET:/api/users:user1:abc123", {"users": []})
        await cache.set("api:GET:/api/users:user1:def456", {"users": []})
        await cache.set("api:GET:/api/posts:user1:abc123", {"posts": []})

        # Invalidate users endpoint
        deleted = await cache_mgr.invalidate_endpoint("/api/users")
        assert deleted >= 2

        # Posts should still be cached
        assert await cache.exists("api:GET:/api/posts:user1:abc123") is True

        # Cleanup
        await cache.clear()
        await cache.disconnect()


class TestCacheKey:
    """Test cache key generation."""

    def test_make_cache_key(self):
        """Test cache key generation."""
        key1 = make_cache_key("api", "v1", "users", 123)
        assert key1 == "api:v1:users:123"

        key2 = make_cache_key("cache", "GET", "/api/posts")
        assert key2 == "cache:GET:/api/posts"

        # Keys should be consistent
        key3 = make_cache_key("api", "v1", "users", 123)
        assert key3 == key1


class TestMiddlewareIntegration:
    """Test middleware integration with FastAPI."""

    def test_rate_limit_middleware(self):
        """Test rate limit middleware integration."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        # Add rate limiting
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=3,
            requests_per_hour=10,
            requests_per_day=20,
        )

        client = TestClient(app)

        # First 3 requests should succeed
        for i in range(3):
            response = client.get("/test")
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers

        # 4th request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_cache_middleware(self):
        """Test cache middleware integration."""
        app = FastAPI()

        call_count = 0

        @app.get("/cached")
        async def cached_endpoint():
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        # Add caching
        app.add_middleware(CacheMiddleware, default_ttl=60)

        client = TestClient(app)

        # First request should hit the endpoint
        response1 = client.get("/cached")
        assert response1.status_code == 200
        assert response1.json()["count"] == 1
        assert response1.headers.get("X-Cache") == "MISS"

        # Second request should be cached
        response2 = client.get("/cached")
        assert response2.status_code == 200
        assert response2.json()["count"] == 1  # Same count!
        assert response2.headers.get("X-Cache") == "HIT"

        # Verify endpoint was only called once
        assert call_count == 1


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration of rate limiting and caching."""
    cache = RedisCache()
    await cache.connect()

    limiter = RedisRateLimiter(requests_per_minute=10)
    cache_mgr = ResponseCache(default_ttl=300)

    # Simulate API request flow
    user_id = "integration_test_user"

    # 1. Check rate limit
    is_allowed, rate_info = await limiter.check_rate_limit(user_id)
    assert is_allowed is True

    # 2. Check cache (miss)
    cache_key = make_cache_key("api", "GET", "/test", "hash123")
    cached = await cache.get(cache_key)
    assert cached is None

    # 3. Execute "request" and cache response
    response_data = {"result": "success", "timestamp": time.time()}
    await cache.set(cache_key, response_data, ttl=300)

    # 4. Verify cache hit
    cached = await cache.get(cache_key)
    assert cached == response_data

    # 5. Verify rate limit stats
    stats = await limiter.get_stats(user_id)
    assert stats["minute"]["count"] == 1

    # Cleanup
    await cache.delete(cache_key)
    await limiter.reset_limit(user_id)
    await cache.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
