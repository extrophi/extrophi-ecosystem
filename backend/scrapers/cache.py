"""Caching layer for scraper results to reduce API calls and improve performance."""

import hashlib
import json
import time
from typing import Any, Optional


class CacheEntry:
    """Single cache entry with expiration."""

    def __init__(self, value: Any, ttl: int):
        """
        Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > self.expires_at


class ScraperCache:
    """
    In-memory cache for scraper results with TTL support.

    Features:
    - TTL-based expiration
    - Platform-specific cache keys
    - Automatic cleanup of expired entries
    - Memory-efficient storage
    """

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default 1 hour)
        """
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}

    def _make_key(self, platform: str, target: str, **kwargs) -> str:
        """
        Generate cache key from parameters.

        Args:
            platform: Platform name (twitter, youtube, etc.)
            target: Target identifier (username, video_id, etc.)
            **kwargs: Additional parameters to include in key

        Returns:
            Hash-based cache key
        """
        key_parts = {
            "platform": platform,
            "target": target,
            **kwargs,
        }

        # Sort keys for consistent hashing
        key_str = json.dumps(key_parts, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]

        return f"{platform}:{key_hash}"

    def get(
        self, platform: str, target: str, **kwargs
    ) -> Optional[list[dict[str, Any]]]:
        """
        Retrieve cached data if available and not expired.

        Args:
            platform: Platform name
            target: Target identifier
            **kwargs: Additional cache key parameters

        Returns:
            Cached data or None if not found/expired
        """
        key = self._make_key(platform, target, **kwargs)

        if key not in self._cache:
            return None

        entry = self._cache[key]

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(
        self,
        platform: str,
        target: str,
        value: list[dict[str, Any]],
        ttl: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Store data in cache.

        Args:
            platform: Platform name
            target: Target identifier
            value: Data to cache
            ttl: Time to live in seconds (uses default if not provided)
            **kwargs: Additional cache key parameters
        """
        key = self._make_key(platform, target, **kwargs)
        ttl = ttl or self.default_ttl

        self._cache[key] = CacheEntry(value, ttl)

    def invalidate(self, platform: str, target: str, **kwargs) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            platform: Platform name
            target: Target identifier
            **kwargs: Additional cache key parameters

        Returns:
            True if entry was removed, False if not found
        """
        key = self._make_key(platform, target, **kwargs)

        if key in self._cache:
            del self._cache[key]
            return True

        return False

    def invalidate_platform(self, platform: str) -> int:
        """
        Invalidate all cache entries for a platform.

        Args:
            platform: Platform name

        Returns:
            Number of entries removed
        """
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{platform}:")]

        for key in keys_to_remove:
            del self._cache[key]

        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_entries = len(self._cache)
        expired_count = sum(1 for v in self._cache.values() if v.is_expired())

        platform_counts: dict[str, int] = {}
        for key in self._cache.keys():
            platform = key.split(":")[0]
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "active_entries": total_entries - expired_count,
            "by_platform": platform_counts,
        }


# Global cache instance
_GLOBAL_CACHE: Optional[ScraperCache] = None


def get_cache(default_ttl: int = 3600) -> ScraperCache:
    """
    Get global cache instance.

    Args:
        default_ttl: Default TTL in seconds (only used on first call)

    Returns:
        ScraperCache instance
    """
    global _GLOBAL_CACHE

    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = ScraperCache(default_ttl=default_ttl)

    return _GLOBAL_CACHE


# Platform-specific TTL configurations (in seconds)
PLATFORM_CACHE_TTL = {
    "twitter": 300,  # 5 minutes (tweets are ephemeral)
    "youtube": 3600,  # 1 hour (transcripts don't change)
    "reddit": 600,  # 10 minutes (posts get updated with comments)
    "web": 7200,  # 2 hours (articles rarely change)
}
