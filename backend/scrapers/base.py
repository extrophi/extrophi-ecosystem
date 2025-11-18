import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MetricsModel(BaseModel):
    """Engagement metrics for content across platforms."""

    likes: int = 0
    views: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0


class AnalysisModel(BaseModel):
    """LLM-generated analysis of content."""

    frameworks: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    keywords: list[str] = Field(default_factory=list)


class AuthorModel(BaseModel):
    """Content author/creator metadata."""

    id: str
    platform: str
    username: str
    display_name: str | None = None


class ContentModel(BaseModel):
    """Core content payload."""

    title: str | None = None
    body: str
    word_count: int = 0


class UnifiedContent(BaseModel):
    """Universal content schema for multi-platform scraping."""

    content_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    platform: str
    source_url: str
    author: AuthorModel
    content: ContentModel
    metrics: MetricsModel = Field(default_factory=MetricsModel)
    analysis: AnalysisModel = Field(default_factory=AnalysisModel)
    embedding: list[float] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseScraper(ABC):
    """
    Abstract base class for platform-specific scrapers.

    Each platform adapter (Twitter, YouTube, Reddit, etc.) inherits from this
    and implements the three core methods: health_check, extract, and normalize.

    This ensures a consistent interface across all scrapers and enables
    modular plugin-style architecture for adding new platforms.
    """

    @abstractmethod
    async def health_check(self) -> dict:
        """
        Verify scraper connectivity and authentication status.

        Returns:
            dict: Status information
                - status: "ok" | "error"
                - message: str
                - timestamp: datetime
                - platform: str

        Example:
            {
                "status": "ok",
                "message": "Twitter API authenticated",
                "timestamp": "2025-11-16T10:30:00Z",
                "platform": "twitter"
            }
        """
        pass

    @abstractmethod
    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract raw content from platform.

        Args:
            target: Platform-specific identifier
                - Twitter: @username
                - YouTube: video_id
                - Reddit: subreddit name
                - Amazon: ASIN
            limit: Max results to fetch (default 20)

        Returns:
            list[dict]: Raw platform-specific data (not yet normalized)

        Example (Twitter):
            [
                {
                    "id": "1234567890",
                    "text": "Hello world",
                    "author_id": "user123",
                    "created_at": "2025-11-16T10:00:00Z",
                    "public_metrics": {"like_count": 42}
                },
                ...
            ]
        """
        pass

    @abstractmethod
    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Convert platform-specific data to UnifiedContent schema.

        Args:
            raw_data: Platform-specific data dict from extract()

        Returns:
            UnifiedContent: Normalized data conforming to unified schema

        Raises:
            ValueError: If raw_data is malformed or missing required fields

        Example (Twitter):
            Input: {"id": "123", "text": "Hello", "author_id": "user1", ...}
            Output: UnifiedContent(
                platform="twitter",
                content=ContentModel(body="Hello", word_count=1),
                author=AuthorModel(id="user1", platform="twitter", ...),
                ...
            )
        """
        pass
