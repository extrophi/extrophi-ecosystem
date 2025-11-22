"""Tests for Naval Ravikant scraper."""

import pytest
from backend.scrapers.adapters.naval import NavalScraper
from backend.scrapers.registry import get_scraper, list_scrapers


class TestNavalScraper:
    """Test suite for Naval Ravikant scraper."""

    @pytest.fixture
    def scraper(self):
        """Create a Naval scraper instance."""
        return NavalScraper()

    def test_scraper_initialization(self, scraper):
        """Test that Naval scraper initializes correctly."""
        assert scraper is not None
        assert scraper.twitter_handle == "naval"
        assert scraper.youtube_query == "Naval Ravikant podcast"
        assert scraper.twitter_scraper is not None
        assert scraper.youtube_scraper is not None

    @pytest.mark.asyncio
    async def test_health_check(self, scraper):
        """Test health check returns correct status."""
        health = await scraper.health_check()

        assert health is not None
        assert "status" in health
        assert "message" in health
        assert "platform" in health
        assert "components" in health
        assert health["platform"] == "naval"
        assert "twitter" in health["components"]
        assert "youtube" in health["components"]

    def test_thread_detection(self, scraper):
        """Test thread detection logic."""
        # Test positive cases
        assert scraper._detect_thread("1/ This is a thread about startups") is True
        assert scraper._detect_thread("Thread: How to build wealth") is True
        assert scraper._detect_thread("🧵 on investing") is True
        assert scraper._detect_thread("1. First point in series") is True

        # Test negative cases
        assert scraper._detect_thread("Just a regular tweet") is False
        assert scraper._detect_thread("No thread indicators here") is False

    def test_content_classification(self, scraper):
        """Test content type classification."""
        # Economics
        assert scraper._classify_content_type("How to build wealth through startups") == "economics"
        assert scraper._classify_content_type("Investing in bitcoin") == "economics"

        # Health
        assert scraper._classify_content_type("Meditation is the key to peace") == "health"
        assert scraper._classify_content_type("Exercise and fitness tips") == "health"

        # Technology
        assert scraper._classify_content_type("Learning to code in Python") == "technology"
        assert scraper._classify_content_type("Building software products") == "technology"

        # Philosophy
        assert scraper._classify_content_type("The meaning of life") == "philosophy"
        assert scraper._classify_content_type("Finding happiness and purpose") == "philosophy"

        # Wisdom (fallback)
        assert scraper._classify_content_type("Random thoughts") == "wisdom"

    def test_scraper_registry(self):
        """Test that Naval scraper is registered."""
        scrapers = list_scrapers()
        assert "naval" in scrapers

        # Test getting scraper from registry
        naval_scraper = get_scraper("naval")
        assert isinstance(naval_scraper, NavalScraper)

    @pytest.mark.asyncio
    async def test_extract_invalid_target(self, scraper):
        """Test that invalid target raises ValueError."""
        with pytest.raises(ValueError, match="Invalid target"):
            await scraper.extract("invalid_platform", limit=10)

    def test_naval_scraper_attributes(self, scraper):
        """Test that Naval scraper has required attributes."""
        # Check twitter scraper
        assert hasattr(scraper, 'twitter_scraper')
        assert hasattr(scraper.twitter_scraper, 'extract')
        assert hasattr(scraper.twitter_scraper, 'normalize')

        # Check youtube scraper
        assert hasattr(scraper, 'youtube_scraper')
        assert hasattr(scraper.youtube_scraper, 'extract')
        assert hasattr(scraper.youtube_scraper, 'normalize')

    @pytest.mark.asyncio
    async def test_normalize_twitter_data(self, scraper):
        """Test normalizing Twitter data adds Naval metadata."""
        raw_twitter_data = {
            "id": "123456789",
            "text": "1/ Thread on wealth creation",
            "author_id": "naval",
            "created_at": "2025-11-22T10:00:00Z",
            "public_metrics": {
                "like_count": 100,
                "retweet_count": 20,
                "reply_count": 5,
            },
            "platform": "twitter",
            "is_thread": True,
        }

        content = await scraper.normalize(raw_twitter_data)

        assert content is not None
        assert content.platform == "twitter"
        assert content.metadata["source"] == "naval"
        assert content.metadata["is_thread"] is True
        assert "content_type" in content.metadata
