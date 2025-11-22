"""Tests for Dan Koe content scraper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.scrapers.adapters.dan_koe import DanKoeScraper


@pytest.fixture
def mock_youtube_data():
    """Mock YouTube video data."""
    return [
        {
            "video_id": "test123",
            "title": "How to Build a Personal Monopoly",
            "transcript": "This is a test transcript about building a personal monopoly...",
            "segments": [],
            "duration": 600,
            "channel": "Dan Koe",
            "channel_id": "UC123456",
            "view_count": 10000,
            "like_count": 500,
            "upload_date": "20231115",
            "description": "Test description",
            "extracted_at": "2023-11-16T10:00:00Z",
        }
    ]


@pytest.fixture
def mock_twitter_data():
    """Mock Twitter/X tweet data."""
    return [
        {
            "id": "1234567890",
            "text": "Building a personal monopoly is the key to success in 2024.",
            "author_id": "thedankoe",
            "created_at": "2023-11-16T10:00:00Z",
            "public_metrics": {
                "like_count": 100,
                "retweet_count": 20,
                "reply_count": 5,
                "view_count": 1000,
            },
        }
    ]


@pytest.fixture
def mock_substack_data():
    """Mock Substack article data."""
    return [
        {
            "url": "https://dankoe.substack.com/p/test-article",
            "title": "The Modern Creator Economy",
            "content": "# The Modern Creator Economy\n\nThis is a test article about the creator economy...",
            "content_type": "markdown",
            "status_code": 200,
            "extracted_at": "2023-11-16T10:00:00Z",
        }
    ]


@pytest.mark.asyncio
async def test_health_check():
    """Test scraper health check."""
    scraper = DanKoeScraper(max_credits=100)
    health = await scraper.health_check()

    assert health["platform"] == "dan_koe"
    assert "scrapers" in health
    assert "youtube" in health["scrapers"]
    assert "twitter" in health["scrapers"]
    assert "web" in health["scrapers"]


@pytest.mark.asyncio
async def test_scrape_youtube(mock_youtube_data):
    """Test YouTube scraping."""
    scraper = DanKoeScraper(max_credits=100)

    with patch.object(
        scraper.youtube_scraper, "extract", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.return_value = mock_youtube_data

        videos = await scraper._scrape_youtube(limit=10)

        assert len(videos) == 1
        assert videos[0]["video_id"] == "test123"
        assert scraper.stats["youtube"]["scraped"] == 1
        assert scraper.credits_used == 1  # 1 video * 1 credit/video


@pytest.mark.asyncio
async def test_scrape_twitter(mock_twitter_data):
    """Test Twitter scraping."""
    scraper = DanKoeScraper(max_credits=100)

    with patch.object(
        scraper.twitter_scraper, "extract", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.return_value = mock_twitter_data

        tweets = await scraper._scrape_twitter(limit=10)

        assert len(tweets) == 1
        assert tweets[0]["id"] == "1234567890"
        assert scraper.stats["twitter"]["scraped"] == 1
        assert scraper.credits_used == 0.5  # 1 tweet * 0.5 credit/tweet


@pytest.mark.asyncio
async def test_credit_limit():
    """Test credit limit enforcement."""
    scraper = DanKoeScraper(max_credits=5)

    # Consume credits
    scraper._consume_credits(3)
    assert not scraper._check_credit_limit()

    scraper._consume_credits(2)
    assert scraper._check_credit_limit()  # Should hit limit

    scraper._consume_credits(1)
    assert scraper._check_credit_limit()  # Should still be over limit


@pytest.mark.asyncio
async def test_extract_all_platforms(mock_youtube_data, mock_twitter_data, mock_substack_data):
    """Test extracting from all platforms."""
    scraper = DanKoeScraper(max_credits=1000)

    with patch.object(
        scraper.youtube_scraper, "extract", new_callable=AsyncMock
    ) as mock_yt, \
         patch.object(
        scraper.twitter_scraper, "extract", new_callable=AsyncMock
    ) as mock_tw, \
         patch.object(
        scraper.web_scraper, "extract", new_callable=AsyncMock
    ) as mock_web:

        mock_yt.return_value = mock_youtube_data
        mock_tw.return_value = mock_twitter_data

        # Mock Substack archive + article
        mock_web.side_effect = [
            [{"content": "[Article 1](https://dankoe.substack.com/p/test-article)"}],
            mock_substack_data,
        ]

        content = await scraper.extract(target="all", limit=10)

        # Should have content from all 3 platforms
        assert len(content) >= 3
        assert scraper.stats["youtube"]["scraped"] == 1
        assert scraper.stats["twitter"]["scraped"] == 1
        assert scraper.stats["substack"]["scraped"] == 1


@pytest.mark.asyncio
async def test_normalize_youtube(mock_youtube_data):
    """Test normalizing YouTube data."""
    scraper = DanKoeScraper(max_credits=100)

    unified = await scraper.normalize(mock_youtube_data[0])

    assert unified.platform == "youtube"
    assert "youtube.com/watch?v=" in unified.source_url
    assert unified.content.title == "How to Build a Personal Monopoly"
    assert "personal monopoly" in unified.content.body.lower()
    assert unified.metrics.views == 10000
    assert unified.metrics.likes == 500


@pytest.mark.asyncio
async def test_normalize_twitter(mock_twitter_data):
    """Test normalizing Twitter data."""
    scraper = DanKoeScraper(max_credits=100)

    unified = await scraper.normalize(mock_twitter_data[0])

    assert unified.platform == "twitter"
    assert "twitter.com" in unified.source_url
    assert "personal monopoly" in unified.content.body.lower()
    assert unified.metrics.likes == 100


@pytest.mark.asyncio
async def test_extract_substack_urls():
    """Test extracting Substack article URLs from archive."""
    scraper = DanKoeScraper(max_credits=100)

    markdown = """
    # Archive

    [Article 1](https://dankoe.substack.com/p/article-1)
    [Article 2](https://dankoe.substack.com/p/article-2)
    [Article 3](https://example.com/not-substack)
    [Article 4](https://dankoe.substack.com/p/article-1)  # Duplicate
    """

    urls = scraper._extract_substack_urls(markdown, limit=10)

    assert len(urls) == 2  # Only unique Substack URLs
    assert "https://dankoe.substack.com/p/article-1" in urls
    assert "https://dankoe.substack.com/p/article-2" in urls
    assert "https://example.com/not-substack" not in urls


@pytest.mark.asyncio
async def test_error_handling_youtube():
    """Test error handling for YouTube scraping."""
    scraper = DanKoeScraper(max_credits=100)

    with patch.object(
        scraper.youtube_scraper, "extract", side_effect=Exception("Network error")
    ):
        videos = await scraper._scrape_youtube(limit=10)

        assert len(videos) == 0
        assert scraper.stats["youtube"]["errors"] == 1
        assert len(scraper.stats["youtube"]["error_details"]) > 0


@pytest.mark.asyncio
async def test_generate_report():
    """Test report generation."""
    scraper = DanKoeScraper(max_credits=100)

    # Simulate some scraping activity
    scraper.stats["youtube"]["scraped"] = 10
    scraper.stats["youtube"]["saved"] = 9
    scraper.stats["youtube"]["errors"] = 1
    scraper.stats["youtube"]["error_details"] = ["Test error"]

    scraper.stats["twitter"]["scraped"] = 50
    scraper.stats["twitter"]["saved"] = 48
    scraper.stats["twitter"]["errors"] = 2

    scraper.credits_used = 35.5

    report = scraper._generate_report()

    assert report["total_scraped"] == 60
    assert report["total_saved"] == 57
    assert report["total_errors"] == 3
    assert report["credits_used"] == 35.5

    assert "Dan Koe Content Scraper Report" in report["summary"]
    assert "YouTube" in report["summary"]
    assert "Twitter" in report["summary"]
    assert "35.50 / 100" in report["summary"]


def test_credit_costs():
    """Test credit cost constants."""
    scraper = DanKoeScraper()

    assert scraper.YOUTUBE_COST_PER_VIDEO == 1
    assert scraper.TWITTER_COST_PER_TWEET == 0.5
    assert scraper.SUBSTACK_COST_PER_ARTICLE == 1


def test_platform_targets():
    """Test platform target constants."""
    scraper = DanKoeScraper()

    assert scraper.YOUTUBE_HANDLE == "@thedankoe"
    assert scraper.TWITTER_HANDLE == "thedankoe"
    assert scraper.SUBSTACK_URL == "https://dankoe.substack.com"


def test_scraping_limits():
    """Test default scraping limits."""
    scraper = DanKoeScraper()

    assert scraper.YOUTUBE_LIMIT == 100
    assert scraper.TWITTER_LIMIT == 1000
    assert scraper.SUBSTACK_LIMIT == 50
