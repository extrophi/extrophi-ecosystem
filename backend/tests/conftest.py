"""Pytest fixtures and configuration."""

import os
from typing import Any
from unittest.mock import MagicMock

import pytest

# Set test environment variables
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8000"
os.environ["OPENAI_API_KEY"] = "test-key"


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Mock database session."""
    session = MagicMock()
    yield session
    session.close()


@pytest.fixture
def sample_tweet_data() -> dict[str, Any]:
    """Sample Twitter data for testing."""
    return {
        "id": "123456789",
        "text": "This is a test tweet about productivity and focus systems.",
        "author_id": "testuser",
        "created_at": "2025-11-16T10:00:00Z",
        "public_metrics": {
            "like_count": 42,
            "retweet_count": 10,
            "reply_count": 5,
        },
    }


@pytest.fixture
def sample_reddit_data() -> dict[str, Any]:
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
        "permalink": "/r/productivity/comments/abc123/...",
    }


@pytest.fixture
def sample_youtube_data() -> dict[str, Any]:
    """Sample YouTube data for testing."""
    return {
        "video_id": "dQw4w9WgXcQ",
        "transcript": "Never gonna give you up, never gonna let you down...",
        "segments": [
            {"text": "Never gonna give you up", "start": 0, "duration": 2},
            {"text": "never gonna let you down", "start": 2, "duration": 2},
        ],
        "duration": 4,
        "extracted_at": "2025-11-16T10:00:00Z",
    }


@pytest.fixture
def sample_analysis_result() -> dict[str, Any]:
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
        "key_insights": ["Focus is key to success"],
    }
