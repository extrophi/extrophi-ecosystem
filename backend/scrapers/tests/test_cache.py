"""Tests for caching functionality."""

import time

import pytest

from backend.scrapers.cache import ScraperCache


class TestScraperCache:
    """Test scraper cache functionality."""

    def test_cache_initialization(self):
        """Test cache initializes with default TTL."""
        cache = ScraperCache(default_ttl=3600)
        assert cache.default_ttl == 3600

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = ScraperCache(default_ttl=60)

        data = [{"id": "1", "text": "test content"}]
        cache.set("twitter", "@testuser", data)

        retrieved = cache.get("twitter", "@testuser")
        assert retrieved == data

    def test_cache_miss(self):
        """Test cache returns None for missing keys."""
        cache = ScraperCache()

        result = cache.get("twitter", "@nonexistent")
        assert result is None

    def test_cache_expiration(self):
        """Test cache entries expire after TTL."""
        cache = ScraperCache(default_ttl=1)

        data = [{"id": "1", "text": "test"}]
        cache.set("twitter", "@testuser", data, ttl=1)

        # Should be available immediately
        assert cache.get("twitter", "@testuser") == data

        # Wait for expiration
        time.sleep(1.1)

        # Should be None after expiration
        assert cache.get("twitter", "@testuser") is None

    def test_cache_custom_ttl(self):
        """Test cache entries can have custom TTL."""
        cache = ScraperCache(default_ttl=60)

        data = [{"id": "1", "text": "test"}]
        cache.set("twitter", "@testuser", data, ttl=2)

        # Should be available
        assert cache.get("twitter", "@testuser") == data

        # Wait for custom TTL expiration
        time.sleep(2.1)

        # Should be expired
        assert cache.get("twitter", "@testuser") is None

    def test_cache_with_kwargs(self):
        """Test cache keys differentiate on kwargs."""
        cache = ScraperCache()

        data1 = [{"id": "1"}]
        data2 = [{"id": "2"}]

        cache.set("twitter", "@user", data1, limit=10)
        cache.set("twitter", "@user", data2, limit=20)

        # Different kwargs should be different cache entries
        assert cache.get("twitter", "@user", limit=10) == data1
        assert cache.get("twitter", "@user", limit=20) == data2

    def test_invalidate_specific_entry(self):
        """Test invalidating specific cache entry."""
        cache = ScraperCache()

        cache.set("twitter", "@user1", [{"id": "1"}])
        cache.set("twitter", "@user2", [{"id": "2"}])

        # Invalidate one entry
        result = cache.invalidate("twitter", "@user1")
        assert result is True

        # Check correct entry removed
        assert cache.get("twitter", "@user1") is None
        assert cache.get("twitter", "@user2") is not None

    def test_invalidate_nonexistent(self):
        """Test invalidating nonexistent entry returns False."""
        cache = ScraperCache()

        result = cache.invalidate("twitter", "@nonexistent")
        assert result is False

    def test_invalidate_platform(self):
        """Test invalidating all entries for a platform."""
        cache = ScraperCache()

        cache.set("twitter", "@user1", [{"id": "1"}])
        cache.set("twitter", "@user2", [{"id": "2"}])
        cache.set("youtube", "video123", [{"id": "3"}])

        # Invalidate all twitter entries
        count = cache.invalidate_platform("twitter")
        assert count == 2

        # Check twitter entries removed, youtube remains
        assert cache.get("twitter", "@user1") is None
        assert cache.get("twitter", "@user2") is None
        assert cache.get("youtube", "video123") is not None

    def test_clear_cache(self):
        """Test clearing all cache entries."""
        cache = ScraperCache()

        cache.set("twitter", "@user1", [{"id": "1"}])
        cache.set("youtube", "video123", [{"id": "2"}])

        cache.clear()

        assert cache.get("twitter", "@user1") is None
        assert cache.get("youtube", "video123") is None

    def test_cleanup_expired(self):
        """Test cleanup removes only expired entries."""
        cache = ScraperCache()

        # Add entries with different TTLs
        cache.set("twitter", "@user1", [{"id": "1"}], ttl=1)
        cache.set("twitter", "@user2", [{"id": "2"}], ttl=60)

        # Wait for first to expire
        time.sleep(1.1)

        # Cleanup
        removed = cache.cleanup_expired()
        assert removed == 1

        # Check correct entry removed
        assert cache.get("twitter", "@user1") is None
        assert cache.get("twitter", "@user2") is not None

    def test_get_stats(self):
        """Test cache statistics."""
        cache = ScraperCache()

        cache.set("twitter", "@user1", [{"id": "1"}], ttl=1)
        cache.set("twitter", "@user2", [{"id": "2"}], ttl=60)
        cache.set("youtube", "video123", [{"id": "3"}], ttl=60)

        # Wait for one to expire
        time.sleep(1.1)

        stats = cache.get_stats()

        assert stats["total_entries"] == 3
        assert stats["expired_entries"] == 1
        assert stats["active_entries"] == 2
        assert stats["by_platform"]["twitter"] == 2
        assert stats["by_platform"]["youtube"] == 1
