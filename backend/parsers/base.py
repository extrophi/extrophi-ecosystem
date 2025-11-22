"""Base parser interface for content analysis."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParsedInsight(BaseModel):
    """Structured insight extracted from content."""

    insight_id: str
    content_id: str
    insight_type: str  # principle, framework, mental_model, quote, pattern
    category: str  # economics, philosophy, technology, health, wisdom
    title: str
    description: str
    source_text: str
    confidence_score: float = 0.0
    tags: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class BaseParser(ABC):
    """
    Abstract base class for content parsers.

    Parsers extract structured insights from scraped content,
    identifying patterns, principles, frameworks, and key concepts.
    """

    @abstractmethod
    async def parse(self, content: Dict[str, Any]) -> List[ParsedInsight]:
        """
        Parse content and extract structured insights.

        Args:
            content: Raw or normalized content dict

        Returns:
            List of ParsedInsight objects
        """
        pass

    @abstractmethod
    async def extract_principles(self, text: str) -> List[str]:
        """Extract core principles from text."""
        pass

    @abstractmethod
    async def extract_frameworks(self, text: str) -> List[str]:
        """Extract mental models and frameworks."""
        pass

    @abstractmethod
    async def categorize(self, text: str) -> str:
        """Categorize content into topics."""
        pass
