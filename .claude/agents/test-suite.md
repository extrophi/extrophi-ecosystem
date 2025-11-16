---
name: test-suite
description: Build comprehensive test suite with pytest. Use PROACTIVELY when building tests.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are a senior Python developer specializing in testing and QA.

## Your Task
Build comprehensive test suite for the unified scraper system.

## Files to Create

### backend/tests/__init__.py
```python
"""Test suite for unified scraper."""
```

### backend/tests/conftest.py
```python
"""Pytest fixtures and configuration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment variables
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8000"
os.environ["OPENAI_API_KEY"] = "test-key"


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    yield session
    session.close()


@pytest.fixture
def sample_tweet_data():
    """Sample Twitter data for testing."""
    return {
        "id": "123456789",
        "text": "This is a test tweet about productivity and focus systems.",
        "author_id": "testuser",
        "created_at": "2025-11-16T10:00:00Z",
        "public_metrics": {
            "like_count": 42,
            "retweet_count": 10,
            "reply_count": 5
        }
    }


@pytest.fixture
def sample_reddit_data():
    """Sample Reddit data for testing."""
    return {
        "id": "abc123",
        "title": "How to improve focus and productivity",
        "selftext": "I've been struggling with focus lately...",
        "author": "testuser",
        "subreddit": "productivity",
        "created_utc": 1700000000,
        "score": 150,
        "upvote_ratio": 0.95,
        "num_comments": 25,
        "url": "https://reddit.com/r/productivity/...",
        "permalink": "/r/productivity/comments/abc123/..."
    }


@pytest.fixture
def sample_youtube_data():
    """Sample YouTube data for testing."""
    return {
        "video_id": "dQw4w9WgXcQ",
        "transcript": "Never gonna give you up, never gonna let you down...",
        "segments": [
            {"text": "Never gonna give you up", "start": 0, "duration": 2},
            {"text": "never gonna let you down", "start": 2, "duration": 2}
        ],
        "duration": 4,
        "extracted_at": "2025-11-16T10:00:00Z"
    }


@pytest.fixture
def sample_analysis_result():
    """Sample LLM analysis result."""
    return {
        "frameworks": ["AIDA", "PAS"],
        "hooks": ["curiosity", "benefit-driven"],
        "themes": ["productivity", "focus", "mindset"],
        "pain_points": ["distraction", "lack of focus"],
        "desires": ["deep work", "productivity"],
        "sentiment": "positive",
        "tone": "inspirational",
        "target_audience": "knowledge workers",
        "call_to_action": "subscribe",
        "key_insights": ["Focus is key to success"]
    }
```

### backend/tests/test_scrapers.py
```python
"""Tests for scraper modules."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.scrapers.base import UnifiedContent, AuthorModel, ContentModel, MetricsModel


class TestBaseScraper:
    """Test BaseScraper interface."""

    def test_unified_content_model(self):
        """Test UnifiedContent Pydantic model."""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/status/123",
            author=AuthorModel(
                id="test_user",
                platform="twitter",
                username="testuser"
            ),
            content=ContentModel(
                body="Test content",
                word_count=2
            )
        )

        assert content.platform == "twitter"
        assert content.author.username == "testuser"
        assert content.content.word_count == 2
        assert content.metrics.likes == 0  # Default

    def test_metrics_model_defaults(self):
        """Test MetricsModel default values."""
        metrics = MetricsModel()
        assert metrics.likes == 0
        assert metrics.views == 0
        assert metrics.engagement_rate == 0.0


class TestTwitterScraper:
    """Test Twitter scraper."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test scraper health check."""
        from backend.scrapers.adapters.twitter import TwitterScraper
        scraper = TwitterScraper()
        result = await scraper.health_check()

        assert result["status"] == "ok"
        assert result["platform"] == "twitter"

    @pytest.mark.asyncio
    async def test_normalize_tweet(self, sample_tweet_data):
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
    async def test_normalize_post(self, sample_reddit_data):
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
    async def test_extract_video_id(self):
        """Test video ID extraction from URL."""
        from backend.scrapers.adapters.youtube import YouTubeScraper
        scraper = YouTubeScraper()

        # Test various URL formats
        assert scraper._extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert scraper._extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert scraper._extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_normalize_transcript(self, sample_youtube_data):
        """Test YouTube transcript normalization."""
        from backend.scrapers.adapters.youtube import YouTubeScraper
        scraper = YouTubeScraper()
        normalized = await scraper.normalize(sample_youtube_data)

        assert normalized.platform == "youtube"
        assert "Never gonna" in normalized.content.body
```

### backend/tests/test_analysis.py
```python
"""Tests for LLM analysis pipeline."""
import pytest
from unittest.mock import patch, MagicMock
import json


class TestContentAnalyzer:
    """Test ContentAnalyzer."""

    @pytest.mark.asyncio
    @patch("openai.ChatCompletion.create")
    async def test_analyze_content(self, mock_openai, sample_analysis_result):
        """Test content analysis with mocked OpenAI."""
        from backend.analysis.analyzer import ContentAnalyzer

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(sample_analysis_result)))
        ]
        mock_openai.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = await analyzer.analyze_content("Test content about focus")

        assert "frameworks" in result
        assert "AIDA" in result["frameworks"]
        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    @patch("openai.ChatCompletion.create")
    async def test_detect_patterns(self, mock_openai):
        """Test pattern detection."""
        from backend.analysis.analyzer import ContentAnalyzer

        pattern_result = {
            "elaboration_patterns": [],
            "recurring_themes": ["focus", "productivity"],
            "preferred_hooks": ["curiosity"],
            "framework_preferences": ["AIDA"],
            "confidence_score": 0.85
        }

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(pattern_result)))
        ]
        mock_openai.return_value = mock_response

        analyzer = ContentAnalyzer()
        content_list = [
            {"platform": "twitter", "body": "Test 1", "id": "1"},
            {"platform": "youtube", "body": "Test 2", "id": "2"}
        ]
        result = await analyzer.detect_patterns(content_list)

        assert "recurring_themes" in result
        assert "focus" in result["recurring_themes"]


class TestAnalysisPrompts:
    """Test analysis prompts."""

    def test_prompts_exist(self):
        """Test that all required prompts are defined."""
        from backend.analysis.prompts import ANALYSIS_PROMPTS

        assert "framework_extraction" in ANALYSIS_PROMPTS
        assert "pattern_detection" in ANALYSIS_PROMPTS
        assert "{content}" in ANALYSIS_PROMPTS["framework_extraction"]
```

### backend/tests/test_api.py
```python
"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture
def client():
    """Create test client."""
    from backend.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_main_health(self, client):
        """Test main health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestScrapeEndpoints:
    """Test scraping endpoints."""

    @patch("backend.api.routes.scrape.get_scraper")
    def test_scrape_invalid_platform(self, mock_get_scraper, client):
        """Test scraping with invalid platform."""
        response = client.post(
            "/scrape/invalid",
            json={"target": "test", "limit": 10}
        )
        assert response.status_code == 400
        assert "Invalid platform" in response.json()["detail"]

    @patch("backend.api.routes.scrape.get_scraper")
    def test_scrape_twitter(self, mock_get_scraper, client):
        """Test Twitter scraping endpoint."""
        mock_scraper = AsyncMock()
        mock_scraper.health_check.return_value = {"status": "ok"}
        mock_scraper.extract.return_value = [{"id": "1", "text": "test"}]
        mock_scraper.normalize.return_value = MagicMock(content_id="uuid-123")
        mock_get_scraper.return_value = mock_scraper

        response = client.post(
            "/scrape/twitter",
            json={"target": "@testuser", "limit": 10}
        )
        assert response.status_code == 200
        assert response.json()["platform"] == "twitter"


class TestQueryEndpoints:
    """Test RAG query endpoints."""

    @patch("backend.api.routes.query.EmbeddingGenerator")
    @patch("backend.api.routes.query.ChromaDBClient")
    def test_rag_query(self, mock_chroma, mock_embedding, client):
        """Test RAG semantic search."""
        mock_embedding_instance = MagicMock()
        mock_embedding_instance.generate.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_instance

        mock_chroma_instance = MagicMock()
        mock_chroma_instance.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"platform": "twitter"}, {"platform": "reddit"}]]
        }
        mock_chroma.return_value = mock_chroma_instance

        response = client.post(
            "/query/rag",
            json={"prompt": "focus systems", "n_results": 5}
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2
```

### pytest.ini
```ini
[pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
```

## Requirements
- pytest and pytest-asyncio
- unittest.mock for mocking
- FastAPI TestClient
- Add to pyproject.toml: pytest, pytest-asyncio, httpx

Write the complete files now.
