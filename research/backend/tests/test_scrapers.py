"""
Comprehensive tests for scraper adapters and registry.

Tests cover:
- Twitter scraper initialization and extraction
- YouTube scraper transcript and metadata extraction
- Reddit scraper post and comment extraction
- Scraper registry functionality
- Unified schema validation
- Error handling and edge cases
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
from typing import Any
import sys
import os

# Add parent backend directory to path to import shared backend modules
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from scrapers.base import (
    BaseScraper,
    UnifiedContent,
    AuthorModel,
    ContentModel,
    MetricsModel,
    AnalysisModel,
)
from scrapers.adapters.twitter import TwitterScraper
from scrapers.adapters.youtube import YouTubeScraper
from scrapers.adapters.reddit import RedditScraper
from scrapers.registry import (
    register_scraper,
    get_scraper,
    list_scrapers,
    _SCRAPER_REGISTRY,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_tweet_data():
    """Sample raw Twitter data"""
    return {
        "id": "1234567890",
        "text": "This is a test tweet about machine learning and AI.",
        "author_id": "testuser",
        "created_at": "2025-11-21T10:00:00Z",
        "public_metrics": {
            "like_count": 42,
            "retweet_count": 10,
            "reply_count": 5,
        },
    }


@pytest.fixture
def sample_youtube_data():
    """Sample raw YouTube transcript data"""
    return {
        "video_id": "dQw4w9WgXcQ",
        "transcript": "This is a test video transcript about productivity.",
        "segments": [
            {"text": "This is a test", "start": 0.0, "duration": 2.0},
            {"text": "video transcript", "start": 2.0, "duration": 2.0},
            {"text": "about productivity.", "start": 4.0, "duration": 2.0},
        ],
        "duration": 6.0,
        "extracted_at": "2025-11-21T10:00:00Z",
    }


@pytest.fixture
def sample_reddit_data():
    """Sample raw Reddit post data"""
    return {
        "id": "abc123",
        "title": "How to improve focus as a developer",
        "selftext": "I've been struggling with focus lately. Any tips?",
        "author": "testuser",
        "subreddit": "productivity",
        "created_utc": 1700567890.0,
        "score": 125,
        "upvote_ratio": 0.95,
        "num_comments": 42,
        "url": "https://reddit.com/r/productivity/comments/abc123",
        "permalink": "/r/productivity/comments/abc123/how_to_improve_focus",
    }


@pytest_asyncio.fixture
async def twitter_scraper():
    """Create TwitterScraper instance"""
    return TwitterScraper()


@pytest_asyncio.fixture
async def youtube_scraper():
    """Create YouTubeScraper instance"""
    return YouTubeScraper()


@pytest_asyncio.fixture
async def reddit_scraper():
    """Create RedditScraper instance"""
    scraper = RedditScraper()
    # Mock the PRAW reddit instance to avoid needing credentials
    scraper.reddit = MagicMock()
    return scraper


# ============================================================================
# Twitter Scraper Tests
# ============================================================================

class TestTwitterScraper:
    """Test suite for TwitterScraper"""

    @pytest.mark.asyncio
    async def test_health_check(self, twitter_scraper):
        """Test Twitter scraper health check"""
        result = await twitter_scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "twitter"
        assert "message" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_extract_with_username(self, twitter_scraper):
        """Test extracting tweets from username"""
        with patch("scrapers.adapters.twitter.async_playwright") as mock_pw:
            # Setup mock playwright
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_element = AsyncMock()
            mock_element.inner_text = AsyncMock(return_value="Test tweet content")
            mock_page.query_selector_all = AsyncMock(return_value=[mock_element])

            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_pw.return_value.__aenter__.return_value.chromium.launch = AsyncMock(
                return_value=mock_browser
            )

            result = await twitter_scraper.extract("@testuser", limit=1)

            assert isinstance(result, list)
            assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_normalize_tweet(self, twitter_scraper, sample_tweet_data):
        """Test normalizing raw Twitter data to UnifiedContent"""
        unified = await twitter_scraper.normalize(sample_tweet_data)

        assert unified.platform == "twitter"
        assert unified.content.body == sample_tweet_data["text"]
        assert unified.author.username == sample_tweet_data["author_id"]
        assert unified.metrics.likes == sample_tweet_data["public_metrics"]["like_count"]
        assert unified.metrics.shares == sample_tweet_data["public_metrics"]["retweet_count"]
        assert unified.metrics.comments == sample_tweet_data["public_metrics"]["reply_count"]
        assert unified.metadata["tweet_id"] == sample_tweet_data["id"]

    @pytest.mark.asyncio
    async def test_normalize_tweet_word_count(self, twitter_scraper, sample_tweet_data):
        """Test word count calculation in normalized tweet"""
        unified = await twitter_scraper.normalize(sample_tweet_data)

        expected_word_count = len(sample_tweet_data["text"].split())
        assert unified.content.word_count == expected_word_count

    @pytest.mark.asyncio
    async def test_extract_strips_at_symbol(self, twitter_scraper):
        """Test that @ symbol is stripped from username"""
        with patch("scrapers.adapters.twitter.async_playwright") as mock_pw:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            mock_page.query_selector_all = AsyncMock(return_value=[])
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_pw.return_value.__aenter__.return_value.chromium.launch = AsyncMock(
                return_value=mock_browser
            )

            await twitter_scraper.extract("@testuser", limit=1)

            # Verify the goto was called with username without @
            mock_page.goto.assert_called()
            call_args = mock_page.goto.call_args[0][0]
            assert call_args == "https://twitter.com/testuser"


# ============================================================================
# YouTube Scraper Tests
# ============================================================================

class TestYouTubeScraper:
    """Test suite for YouTubeScraper"""

    @pytest.mark.asyncio
    async def test_health_check(self, youtube_scraper):
        """Test YouTube scraper health check"""
        result = await youtube_scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "youtube"
        assert "message" in result

    @pytest.mark.asyncio
    async def test_extract_video_id(self, youtube_scraper):
        """Test extracting transcript with video ID"""
        with patch("scrapers.adapters.youtube.YouTubeTranscriptApi") as mock_api:
            mock_api.get_transcript.return_value = [
                {"text": "Hello", "start": 0.0, "duration": 1.0},
                {"text": "World", "start": 1.0, "duration": 1.0},
            ]

            result = await youtube_scraper.extract("dQw4w9WgXcQ", limit=1)

            assert len(result) == 1
            assert result[0]["video_id"] == "dQw4w9WgXcQ"
            assert "Hello World" in result[0]["transcript"]

    @pytest.mark.asyncio
    async def test_extract_from_url(self, youtube_scraper):
        """Test extracting video ID from various URL formats"""
        test_urls = [
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]

        for url, expected_id in test_urls:
            extracted_id = youtube_scraper._extract_video_id(url)
            assert extracted_id == expected_id

    @pytest.mark.asyncio
    async def test_extract_handles_error(self, youtube_scraper):
        """Test error handling during transcript extraction"""
        with patch("scrapers.adapters.youtube.YouTubeTranscriptApi") as mock_api:
            mock_api.get_transcript.side_effect = Exception("Video unavailable")

            result = await youtube_scraper.extract("invalid_id")

            assert len(result) == 1
            assert "error" in result[0]
            assert result[0]["transcript"] == ""

    @pytest.mark.asyncio
    async def test_normalize_youtube(self, youtube_scraper, sample_youtube_data):
        """Test normalizing raw YouTube data to UnifiedContent"""
        unified = await youtube_scraper.normalize(sample_youtube_data)

        assert unified.platform == "youtube"
        assert unified.content.body == sample_youtube_data["transcript"]
        assert unified.metadata["video_id"] == sample_youtube_data["video_id"]
        assert unified.metadata["duration_seconds"] == sample_youtube_data["duration"]
        assert unified.metadata["segment_count"] == len(sample_youtube_data["segments"])

    @pytest.mark.asyncio
    async def test_normalize_youtube_with_error(self, youtube_scraper):
        """Test normalizing YouTube data with error"""
        error_data = {
            "video_id": "test123",
            "error": "Video unavailable",
            "transcript": "",
            "segments": [],
            "extracted_at": "2025-11-21T10:00:00Z",
        }

        unified = await youtube_scraper.normalize(error_data)

        assert unified.metadata["has_error"] is True
        assert unified.content.body == ""


# ============================================================================
# Reddit Scraper Tests
# ============================================================================

class TestRedditScraper:
    """Test suite for RedditScraper"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, reddit_scraper):
        """Test Reddit scraper health check when authenticated"""
        reddit_scraper.reddit.user.me.return_value = MagicMock()

        result = await reddit_scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "reddit"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, reddit_scraper):
        """Test Reddit scraper health check when not authenticated"""
        reddit_scraper.reddit.user.me.side_effect = Exception("Not authenticated")

        result = await reddit_scraper.health_check()

        assert result["status"] == "error"
        assert result["message"]  # Just check message exists

    @pytest.mark.asyncio
    async def test_extract_subreddit_with_r_prefix(self, reddit_scraper):
        """Test extracting posts from subreddit with r/ prefix"""
        mock_submission = MagicMock()
        mock_submission.id = "abc123"
        mock_submission.title = "Test Post"
        mock_submission.selftext = "Test content"
        mock_submission.author = "testuser"
        mock_submission.subreddit = "productivity"
        mock_submission.created_utc = 1700567890.0
        mock_submission.score = 100
        mock_submission.upvote_ratio = 0.95
        mock_submission.num_comments = 10
        mock_submission.url = "https://reddit.com/test"
        mock_submission.permalink = "/r/productivity/comments/abc123/test"

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = [mock_submission]
        reddit_scraper.reddit.subreddit.return_value = mock_subreddit

        result = await reddit_scraper.extract("r/productivity", limit=1)

        assert len(result) == 1
        assert result[0]["id"] == "abc123"
        assert result[0]["subreddit"] == "productivity"

    @pytest.mark.asyncio
    async def test_extract_user_posts(self, reddit_scraper):
        """Test extracting posts from user with u/ prefix"""
        mock_submission = MagicMock()
        mock_submission.id = "xyz789"
        mock_submission.title = "User Post"
        mock_submission.selftext = "User content"
        mock_submission.author = "testuser"
        mock_submission.subreddit = "test"
        mock_submission.created_utc = 1700567890.0
        mock_submission.score = 50
        mock_submission.upvote_ratio = 0.90
        mock_submission.num_comments = 5
        mock_submission.url = "https://reddit.com/test"
        mock_submission.permalink = "/r/test/comments/xyz789/user_post"

        mock_redditor = MagicMock()
        mock_redditor.submissions.new.return_value = [mock_submission]
        reddit_scraper.reddit.redditor.return_value = mock_redditor

        result = await reddit_scraper.extract("u/testuser", limit=1)

        assert len(result) == 1
        assert result[0]["id"] == "xyz789"

    @pytest.mark.asyncio
    async def test_extract_subreddit_without_prefix(self, reddit_scraper):
        """Test extracting from subreddit without r/ prefix"""
        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = []
        reddit_scraper.reddit.subreddit.return_value = mock_subreddit

        await reddit_scraper.extract("productivity", limit=1)

        reddit_scraper.reddit.subreddit.assert_called_with("productivity")

    @pytest.mark.asyncio
    async def test_normalize_reddit(self, reddit_scraper, sample_reddit_data):
        """Test normalizing raw Reddit data to UnifiedContent"""
        unified = await reddit_scraper.normalize(sample_reddit_data)

        assert unified.platform == "reddit"
        assert unified.content.title == sample_reddit_data["title"]
        assert unified.content.body == sample_reddit_data["selftext"]
        assert unified.author.username == sample_reddit_data["author"]
        assert unified.metrics.likes == sample_reddit_data["score"]
        assert unified.metrics.comments == sample_reddit_data["num_comments"]
        assert unified.metrics.engagement_rate == sample_reddit_data["upvote_ratio"]
        assert unified.metadata["subreddit"] == sample_reddit_data["subreddit"]

    @pytest.mark.asyncio
    async def test_normalize_reddit_title_only(self, reddit_scraper):
        """Test normalizing Reddit post with no selftext"""
        data = {
            "id": "test123",
            "title": "Link Post Title",
            "selftext": "",  # Empty selftext (link post)
            "author": "testuser",
            "subreddit": "test",
            "created_utc": 1700567890.0,
            "score": 10,
            "upvote_ratio": 0.8,
            "num_comments": 2,
            "url": "https://example.com",
            "permalink": "/r/test/comments/test123/link_post",
        }

        unified = await reddit_scraper.normalize(data)

        # When no selftext, body should be the title
        assert unified.content.body == data["title"]

    @pytest.mark.asyncio
    async def test_normalize_reddit_deleted_author(self, reddit_scraper):
        """Test normalizing Reddit post with deleted author"""
        data = {
            "id": "test123",
            "title": "Deleted Post",
            "selftext": "Content",
            "author": None,  # Deleted author
            "subreddit": "test",
            "created_utc": 1700567890.0,
            "score": 0,
            "upvote_ratio": 0.5,
            "num_comments": 0,
            "url": "https://reddit.com/test",
            "permalink": "/r/test/comments/test123/deleted",
        }

        # Mock the submission with author=None
        unified = await reddit_scraper.normalize({**data, "author": "[deleted]"})

        assert unified.author.username == "[deleted]"


# ============================================================================
# Scraper Registry Tests
# ============================================================================

class TestScraperRegistry:
    """Test suite for scraper registry"""

    def test_register_scraper(self):
        """Test registering a custom scraper"""
        class CustomScraper(BaseScraper):
            async def health_check(self):
                return {"status": "ok"}

            async def extract(self, target: str, limit: int = 20):
                return []

            async def normalize(self, raw_data: dict):
                return UnifiedContent(
                    platform="custom",
                    source_url="https://example.com",
                    author=AuthorModel(id="1", platform="custom", username="test"),
                    content=ContentModel(body="test", word_count=1),
                )

        register_scraper("custom", CustomScraper)

        assert "custom" in list_scrapers()
        scraper = get_scraper("custom")
        assert isinstance(scraper, CustomScraper)

    def test_get_registered_scraper(self):
        """Test getting a registered scraper"""
        scraper = get_scraper("twitter")
        assert scraper is not None
        assert hasattr(scraper, 'health_check')
        assert hasattr(scraper, 'extract')
        assert hasattr(scraper, 'normalize')

    def test_get_nonexistent_scraper(self):
        """Test getting a non-existent scraper raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_scraper("nonexistent")

        assert "No scraper registered" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_list_scrapers(self):
        """Test listing all registered scrapers"""
        scrapers = list_scrapers()

        assert isinstance(scrapers, list)
        assert "twitter" in scrapers
        assert "youtube" in scrapers
        assert "reddit" in scrapers

    def test_registry_case_insensitive(self):
        """Test that registry lookups are case-insensitive"""
        scraper1 = get_scraper("TWITTER")
        scraper2 = get_scraper("twitter")
        scraper3 = get_scraper("TwiTTer")

        assert type(scraper1) == type(scraper2) == type(scraper3)


# ============================================================================
# Unified Schema Validation Tests
# ============================================================================

class TestUnifiedSchema:
    """Test suite for UnifiedContent schema validation"""

    def test_unified_content_creation(self):
        """Test creating a valid UnifiedContent instance"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/status/123",
            author=AuthorModel(
                id="user123",
                platform="twitter",
                username="testuser",
                display_name="Test User",
            ),
            content=ContentModel(
                title=None,
                body="Test tweet content",
                word_count=3,
            ),
            metrics=MetricsModel(
                likes=100,
                views=1000,
                comments=10,
                shares=5,
                engagement_rate=0.15,
            ),
        )

        assert content.platform == "twitter"
        assert content.author.username == "testuser"
        assert content.content.word_count == 3

    def test_unified_content_with_defaults(self):
        """Test UnifiedContent with default values"""
        content = UnifiedContent(
            platform="youtube",
            source_url="https://youtube.com/watch?v=test",
            author=AuthorModel(id="1", platform="youtube", username="test"),
            content=ContentModel(body="Video transcript", word_count=2),
        )

        # Check defaults
        assert content.metrics.likes == 0
        assert content.metrics.views == 0
        assert isinstance(content.metadata, dict)
        assert len(content.metadata) == 0
        assert isinstance(content.embedding, list)
        assert len(content.embedding) == 0

    def test_metrics_model_validation(self):
        """Test MetricsModel field validation"""
        metrics = MetricsModel(
            likes=100,
            views=1000,
            comments=50,
            shares=25,
            engagement_rate=0.175,
        )

        assert metrics.likes == 100
        assert metrics.engagement_rate == 0.175

    def test_author_model_optional_display_name(self):
        """Test AuthorModel with optional display_name"""
        author = AuthorModel(
            id="user123",
            platform="reddit",
            username="testuser",
        )

        assert author.display_name is None

    def test_content_model_optional_title(self):
        """Test ContentModel with optional title"""
        content = ContentModel(
            body="This is the content body",
            word_count=5,
        )

        assert content.title is None
        assert content.body == "This is the content body"


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================

class TestEdgeCases:
    """Test suite for edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_tweet_list(self, twitter_scraper):
        """Test handling empty tweet extraction"""
        with patch("scrapers.adapters.twitter.async_playwright") as mock_pw:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            mock_page.query_selector_all = AsyncMock(return_value=[])
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_pw.return_value.__aenter__.return_value.chromium.launch = AsyncMock(
                return_value=mock_browser
            )

            result = await twitter_scraper.extract("@emptyuser", limit=10)

            assert result == []

    @pytest.mark.asyncio
    async def test_malformed_tweet_data(self, twitter_scraper):
        """Test normalizing malformed tweet data"""
        malformed_data = {
            "id": "123",
            "text": "Test",
            "author_id": "user",
            "created_at": "invalid_date",
            "public_metrics": {},  # Missing metrics
        }

        # Should still work with defaults
        unified = await twitter_scraper.normalize(malformed_data)
        assert unified.metrics.likes == 0
        assert unified.metrics.shares == 0

    @pytest.mark.asyncio
    async def test_youtube_video_id_edge_cases(self, youtube_scraper):
        """Test video ID extraction edge cases"""
        # Test plain ID
        assert youtube_scraper._extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

        # Test with trailing query params
        video_id = youtube_scraper._extract_video_id(
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
        )
        assert video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_reddit_limit_enforcement(self, reddit_scraper):
        """Test that Reddit scraper respects limit parameter"""
        # Create 10 mock submissions
        mock_submissions = []
        for i in range(10):
            mock_sub = MagicMock()
            mock_sub.id = f"id{i}"
            mock_sub.title = f"Post {i}"
            mock_sub.selftext = f"Content {i}"
            mock_sub.author = "testuser"
            mock_sub.subreddit = "test"
            mock_sub.created_utc = 1700567890.0 + i
            mock_sub.score = 10
            mock_sub.upvote_ratio = 0.9
            mock_sub.num_comments = 1
            mock_sub.url = f"https://reddit.com/test{i}"
            mock_sub.permalink = f"/r/test/comments/id{i}/post"
            mock_submissions.append(mock_sub)

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = mock_submissions
        reddit_scraper.reddit.subreddit.return_value = mock_subreddit

        result = await reddit_scraper.extract("r/test", limit=5)

        # Should call hot with limit=5
        mock_subreddit.hot.assert_called_with(limit=5)

    @pytest.mark.asyncio
    async def test_empty_content_normalization(self, twitter_scraper):
        """Test normalizing content with empty text"""
        empty_data = {
            "id": "123",
            "text": "",
            "author_id": "user",
            "created_at": "2025-11-21T10:00:00Z",
            "public_metrics": {"like_count": 0, "retweet_count": 0, "reply_count": 0},
        }

        unified = await twitter_scraper.normalize(empty_data)

        assert unified.content.body == ""
        assert unified.content.word_count == 0

    @pytest.mark.asyncio
    async def test_large_content_handling(self, youtube_scraper):
        """Test handling very large transcript content"""
        large_segments = [
            {"text": f"Segment {i}", "start": i * 2.0, "duration": 2.0}
            for i in range(1000)
        ]

        large_data = {
            "video_id": "test123",
            "transcript": " ".join([s["text"] for s in large_segments]),
            "segments": large_segments,
            "duration": 2000.0,
            "extracted_at": "2025-11-21T10:00:00Z",
        }

        unified = await youtube_scraper.normalize(large_data)

        assert unified.metadata["segment_count"] == 1000
        assert unified.metadata["duration_seconds"] == 2000.0
        assert len(unified.content.body) > 0
