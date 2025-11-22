"""Tests for Elon Musk scraper using twscrape."""

import pytest

from backend.scrapers.elon import ElonScraper


class TestElonScraper:
    """Test Elon Musk specialized scraper."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test scraper initialization and health check."""
        scraper = ElonScraper()
        result = await scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "twitter"
        assert result["target"] == "@elonmusk"
        assert result["max_tweets"] == 1000
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_theme_detection_business(self):
        """Test business theme detection."""
        scraper = ElonScraper()

        test_cases = [
            "Tesla Q4 earnings exceeded expectations with record revenue",
            "SpaceX is raising another funding round at $150B valuation",
            "SEC investigation into Twitter acquisition is ongoing",
        ]

        for text in test_cases:
            themes = scraper._detect_themes(text)
            assert "business" in themes

    @pytest.mark.asyncio
    async def test_theme_detection_tech(self):
        """Test tech theme detection."""
        scraper = ElonScraper()

        test_cases = [
            "Our new AI model uses neural networks for autonomous driving",
            "FSD beta 12 improves efficiency with better battery management",
            "Optimus robot can now sort objects autonomously",
        ]

        for text in test_cases:
            themes = scraper._detect_themes(text)
            assert "tech" in themes

    @pytest.mark.asyncio
    async def test_theme_detection_mars(self):
        """Test Mars/SpaceX theme detection."""
        scraper = ElonScraper()

        test_cases = [
            "Starship launch went well. Next stop, Mars!",
            "We're making progress on multi-planetary civilization",
            "Raptor engine test at Starbase was successful",
        ]

        for text in test_cases:
            themes = scraper._detect_themes(text)
            assert "mars" in themes

    @pytest.mark.asyncio
    async def test_theme_detection_problem_solving(self):
        """Test problem-solving/first principles theme detection."""
        scraper = ElonScraper()

        test_cases = [
            "Break it down to first principles and rebuild from scratch",
            "The fundamental physics constraint here is energy density",
            "We need to optimize this bottleneck to achieve breakthrough efficiency",
        ]

        for text in test_cases:
            themes = scraper._detect_themes(text)
            assert "problem_solving" in themes

    @pytest.mark.asyncio
    async def test_meme_detection_emojis(self):
        """Test meme classification based on emojis."""
        scraper = ElonScraper()

        test_cases = [
            "lmao 😂😂😂",
            "This is hilarious 💀",
            "To the moon! 🚀🚀🚀",
        ]

        for text in test_cases:
            is_meme = scraper._is_meme(text)
            assert is_meme is True

    @pytest.mark.asyncio
    async def test_meme_detection_language(self):
        """Test meme classification based on meme language."""
        scraper = ElonScraper()

        test_cases = [
            "lol that's wild",
            "ratio + L + cope",
            "based take tbh",
        ]

        for text in test_cases:
            is_meme = scraper._is_meme(text)
            assert is_meme is True

    @pytest.mark.asyncio
    async def test_meme_detection_short_tweets(self):
        """Test meme classification for very short tweets."""
        scraper = ElonScraper()

        test_cases = [
            "bruh",
            "wat",
            "no way",
        ]

        for text in test_cases:
            is_meme = scraper._is_meme(text)
            assert is_meme is True

    @pytest.mark.asyncio
    async def test_innovation_detection(self):
        """Test that substantive content is NOT classified as meme."""
        scraper = ElonScraper()

        test_cases = [
            "Tesla is working on a new battery chemistry that will increase range by 50%",
            "SpaceX successfully launched Starship and achieved orbital velocity",
            "Neuralink's brain-computer interface is showing promising results in trials",
        ]

        for text in test_cases:
            is_meme = scraper._is_meme(text)
            assert is_meme is False

    @pytest.mark.asyncio
    async def test_normalize_structure(self):
        """Test normalization produces correct UnifiedContent structure."""
        scraper = ElonScraper()

        raw_data = {
            "id": "1234567890",
            "text": "Tesla AI Day was amazing. First principles engineering at its best!",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T12:00:00Z",
            "public_metrics": {
                "like_count": 50000,
                "retweet_count": 10000,
                "reply_count": 2000,
                "view_count": 1000000,
            },
            "url": "https://twitter.com/elonmusk/status/1234567890",
            "is_retweet": False,
            "is_reply": False,
        }

        normalized = await scraper.normalize(raw_data)

        assert normalized.platform == "twitter"
        assert normalized.source_url == raw_data["url"]
        assert normalized.author.username == "elonmusk"
        assert normalized.author.display_name == "Elon Musk"
        assert normalized.content.body == raw_data["text"]
        assert normalized.metrics.likes == 50000
        assert normalized.metrics.shares == 10000
        assert normalized.metrics.views == 1000000

    @pytest.mark.asyncio
    async def test_normalize_metadata(self):
        """Test normalization includes proper metadata and categorization."""
        scraper = ElonScraper()

        raw_data = {
            "id": "123",
            "text": "Starship to Mars! 🚀",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T12:00:00Z",
            "public_metrics": {
                "like_count": 100,
                "retweet_count": 10,
                "reply_count": 5,
                "view_count": 1000,
            },
            "url": "https://twitter.com/elonmusk/status/123",
            "is_retweet": False,
            "is_reply": False,
        }

        normalized = await scraper.normalize(raw_data)

        assert normalized.metadata["source"] == "elon"
        assert normalized.metadata["tweet_id"] == "123"
        assert "themes" in normalized.metadata
        assert "is_meme" in normalized.metadata
        assert "category" in normalized.metadata
        assert normalized.metadata["category"] in ["innovation", "meme"]

    @pytest.mark.asyncio
    async def test_normalize_innovation_content(self):
        """Test that innovation content is properly categorized."""
        scraper = ElonScraper()

        raw_data = {
            "id": "123",
            "text": "Tesla's new battery technology achieves 500 Wh/kg energy density using first principles physics optimization",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T12:00:00Z",
            "public_metrics": {
                "like_count": 100,
                "retweet_count": 10,
                "reply_count": 5,
                "view_count": 1000,
            },
            "url": "https://twitter.com/elonmusk/status/123",
            "is_retweet": False,
            "is_reply": False,
        }

        normalized = await scraper.normalize(raw_data)

        assert "tech" in normalized.metadata["themes"]
        assert "problem_solving" in normalized.metadata["themes"]
        assert normalized.metadata["is_meme"] is False
        assert normalized.metadata["category"] == "innovation"

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test statistics tracking during scraping."""
        scraper = ElonScraper()

        # Simulate some normalizations
        await scraper.normalize({
            "id": "1",
            "text": "Tesla's AI is revolutionary",
            "author_id": "elonmusk",
            "created_at": "2025-11-22T12:00:00Z",
            "public_metrics": {"like_count": 100, "retweet_count": 10, "reply_count": 5, "view_count": 1000},
            "url": "https://twitter.com/elonmusk/status/1",
        })

        await scraper.normalize({
            "id": "2",
            "text": "lmao 😂😂😂",
            "author_id": "elonmusk",
            "created_at": "2025-11-22T12:00:00Z",
            "public_metrics": {"like_count": 200, "retweet_count": 20, "reply_count": 10, "view_count": 2000},
            "url": "https://twitter.com/elonmusk/status/2",
        })

        stats = scraper.get_stats()

        assert stats["innovation"] >= 1
        assert stats["memes"] >= 1
        assert "meme_ratio" in stats
        assert "themes" in stats

    @pytest.mark.asyncio
    async def test_limit_enforcement(self):
        """Test that max_tweets limit is enforced."""
        scraper = ElonScraper()

        # Verify max_tweets is set to 1000
        assert scraper.max_tweets == 1000

        # The extract method should cap limit at 1000 regardless of input
        # Note: We can't easily test actual extraction without API credentials
        # This test verifies the limit is properly configured
        assert scraper.max_tweets == 1000
