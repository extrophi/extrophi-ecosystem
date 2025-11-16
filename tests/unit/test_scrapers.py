"""Tests for scraper modules."""
from typing import Any

import pytest

from backend.scrapers.base import (
    AuthorModel,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class TestBaseScraper:
    """Test BaseScraper interface."""

    def test_unified_content_model(self) -> None:
        """Test UnifiedContent Pydantic model."""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/status/123",
            author=AuthorModel(
                id="test_user", platform="twitter", username="testuser"
            ),
            content=ContentModel(body="Test content", word_count=2),
        )

        assert content.platform == "twitter"
        assert content.author.username == "testuser"
        assert content.content.word_count == 2
        assert content.metrics.likes == 0  # Default

    def test_metrics_model_defaults(self) -> None:
        """Test MetricsModel default values."""
        metrics = MetricsModel()
        assert metrics.likes == 0
        assert metrics.views == 0
        assert metrics.engagement_rate == 0.0


class TestTwitterScraper:
    """Test Twitter scraper."""

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test scraper health check."""
        from backend.scrapers.adapters.twitter import TwitterScraper

        scraper = TwitterScraper()
        result = await scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "twitter"

    @pytest.mark.asyncio
    async def test_normalize_tweet(self, sample_tweet_data: dict[str, Any]) -> None:
        """Test tweet normalization."""
        from backend.scrapers.adapters.twitter import TwitterScraper

        scraper = TwitterScraper()
        normalized = await scraper.normalize(sample_tweet_data)

        assert normalized.platform == "twitter"
        assert normalized.author.username == "testuser"
        assert "productivity" in normalized.content.body


class TestRedditScraper:
    """Test Reddit scraper."""

    @pytest.mark.asyncio
    async def test_normalize_post(self, sample_reddit_data: dict[str, Any]) -> None:
        """Test Reddit post normalization."""
        from backend.scrapers.adapters.reddit import RedditScraper

        scraper = RedditScraper()
        normalized = await scraper.normalize(sample_reddit_data)

        assert normalized.platform == "reddit"
        assert normalized.author.username == "testuser"
        assert normalized.metrics.likes == 150


class TestYouTubeScraper:
    """Test YouTube scraper."""

    @pytest.mark.asyncio
    async def test_extract_video_id(self) -> None:
        """Test video ID extraction from URL."""
        from backend.scrapers.adapters.youtube import YouTubeScraper

        scraper = YouTubeScraper()

        # Test various URL formats
        assert scraper._extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert (
            scraper._extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ")
            == "dQw4w9WgXcQ"
        )
        assert (
            scraper._extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        )

    @pytest.mark.asyncio
    async def test_normalize_transcript(
        self, sample_youtube_data: dict[str, Any]
    ) -> None:
        """Test YouTube transcript normalization."""
        from backend.scrapers.adapters.youtube import YouTubeScraper

        scraper = YouTubeScraper()
        normalized = await scraper.normalize(sample_youtube_data)

        assert normalized.platform == "youtube"
        assert "Never gonna" in normalized.content.body
