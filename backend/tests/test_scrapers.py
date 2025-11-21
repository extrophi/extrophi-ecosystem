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
            author=AuthorModel(id="test_user", platform="twitter", username="testuser"),
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
        assert normalized.metrics.likes == 42
        assert normalized.metrics.shares == 10

    def test_parse_count(self) -> None:
        """Test metric count parsing."""
        from backend.scrapers.adapters.twitter import TwitterScraper

        scraper = TwitterScraper()

        # Test various formats
        assert scraper._parse_count("1.2K") == 1200
        assert scraper._parse_count("2.5M") == 2500000
        assert scraper._parse_count("500") == 500
        assert scraper._parse_count("") == 0
        assert scraper._parse_count("invalid") == 0

    def test_random_delay(self) -> None:
        """Test random delay generation."""
        from backend.scrapers.adapters.twitter import TwitterScraper

        scraper = TwitterScraper()
        delay = scraper._random_delay()

        # Should be between 500 and 1500
        assert 500 <= delay <= 1500


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
        assert scraper._extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert scraper._extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_normalize_transcript(self, sample_youtube_data: dict[str, Any]) -> None:
        """Test YouTube transcript normalization."""
        from backend.scrapers.adapters.youtube import YouTubeScraper

        scraper = YouTubeScraper()
        normalized = await scraper.normalize(sample_youtube_data)

        assert normalized.platform == "youtube"
        assert "Never gonna" in normalized.content.body

    @pytest.mark.asyncio
    async def test_normalize_with_metadata(self) -> None:
        """Test YouTube normalization with full metadata."""
        from backend.scrapers.adapters.youtube import YouTubeScraper

        scraper = YouTubeScraper()

        # Sample data with full metadata (from yt-dlp)
        data = {
            "video_id": "dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up",
            "transcript": "Never gonna give you up...",
            "segments": [],
            "duration": 212,
            "channel": "Rick Astley",
            "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
            "view_count": 1000000000,
            "like_count": 10000000,
            "upload_date": "20091025",
            "description": "Official video",
            "extracted_at": "2025-11-16T10:00:00Z",
        }

        normalized = await scraper.normalize(data)

        assert normalized.platform == "youtube"
        assert normalized.content.title == "Rick Astley - Never Gonna Give You Up"
        assert normalized.author.username == "Rick Astley"
        assert normalized.author.id == "UCuAXFkgsw1L7xaCfnd5JJOw"
        assert normalized.metrics.views == 1000000000
        assert normalized.metrics.likes == 10000000
        # Check engagement rate calculation
        assert normalized.metrics.engagement_rate == pytest.approx(1.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test YouTube scraper health check."""
        from backend.scrapers.adapters.youtube import YouTubeScraper

        scraper = YouTubeScraper()
        result = await scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "youtube"


class TestScraperRegistry:
    """Test scraper registry functionality."""

    def test_registry_has_all_platforms(self) -> None:
        """Test that all platforms are registered."""
        from backend.scrapers.registry import list_scrapers

        scrapers = list_scrapers()

        assert "twitter" in scrapers
        assert "youtube" in scrapers
        assert "reddit" in scrapers

    def test_get_scraper_twitter(self) -> None:
        """Test getting Twitter scraper from registry."""
        from backend.scrapers.adapters.twitter import TwitterScraper
        from backend.scrapers.registry import get_scraper

        scraper = get_scraper("twitter")
        assert isinstance(scraper, TwitterScraper)

    def test_get_scraper_youtube(self) -> None:
        """Test getting YouTube scraper from registry."""
        from backend.scrapers.adapters.youtube import YouTubeScraper
        from backend.scrapers.registry import get_scraper

        scraper = get_scraper("youtube")
        assert isinstance(scraper, YouTubeScraper)

    def test_get_scraper_reddit(self) -> None:
        """Test getting Reddit scraper from registry."""
        from backend.scrapers.adapters.reddit import RedditScraper
        from backend.scrapers.registry import get_scraper

        scraper = get_scraper("reddit")
        assert isinstance(scraper, RedditScraper)

    def test_get_scraper_invalid(self) -> None:
        """Test error handling for invalid platform."""
        from backend.scrapers.registry import get_scraper

        with pytest.raises(ValueError, match="No scraper registered"):
            get_scraper("invalid_platform")
