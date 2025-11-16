"""Pytest configuration and shared fixtures for unit tests."""
import os
import sys
from typing import Any

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Set test environment variables
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CHROMA_HOST", "localhost")
os.environ.setdefault("CHROMA_PORT", "8000")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("REDDIT_CLIENT_ID", "test-client-id")
os.environ.setdefault("REDDIT_CLIENT_SECRET", "test-secret")


@pytest.fixture
def sample_tweet_data() -> dict[str, Any]:
    """Sample tweet data for testing."""
    return {
        "id": "123456789",
        "text": "This is a test tweet about productivity and focus systems.",
        "author_id": "testuser",
        "created_at": "2024-01-01T00:00:00Z",
        "public_metrics": {
            "like_count": 100,
            "retweet_count": 25,
            "reply_count": 10,
        },
    }


@pytest.fixture
def sample_reddit_data() -> dict[str, Any]:
    """Sample Reddit post data for testing."""
    return {
        "id": "abc123",
        "title": "How to improve focus as a developer",
        "selftext": "I've been struggling with focus lately...",
        "author": "testuser",
        "subreddit": "productivity",
        "score": 150,
        "upvote_ratio": 0.95,
        "num_comments": 42,
        "created_utc": 1704067200,
        "permalink": "/r/productivity/comments/abc123/how_to_improve_focus/",
        "url": "https://reddit.com/r/productivity/comments/abc123/",
    }


@pytest.fixture
def sample_youtube_data() -> dict[str, Any]:
    """Sample YouTube transcript data for testing."""
    return {
        "video_id": "dQw4w9WgXcQ",
        "title": "Test Video",
        "transcript": [
            {"text": "Never gonna give you up", "start": 0.0, "duration": 2.0},
            {"text": "Never gonna let you down", "start": 2.0, "duration": 2.0},
        ],
        "duration": 4.0,
    }


@pytest.fixture
def sample_analysis_result() -> dict[str, Any]:
    """Sample LLM analysis result for testing."""
    return {
        "frameworks": ["AIDA", "PAS"],
        "hooks": ["curiosity", "benefit"],
        "themes": ["productivity", "focus"],
        "pain_points": ["distraction", "lack of time"],
        "desires": ["efficiency", "deep work"],
        "sentiment": "positive",
        "tone": "educational",
        "target_audience": "knowledge workers",
        "cta": "Try the 2-hour focus block method",
    }
