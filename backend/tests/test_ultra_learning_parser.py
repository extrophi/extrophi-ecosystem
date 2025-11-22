"""Tests for Ultra Learning Parser"""

import json
import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.models import Base, ContentORM, UltraLearningORM
from backend.services.ultra_learning_parser import UltraLearningParser


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_content(test_db):
    """Create sample content for testing."""
    content = ContentORM(
        id=uuid4(),
        platform="youtube",
        source_url="https://youtube.com/watch?v=test123",
        author_id="channel_123",
        content_title="How to Build an Audience",
        content_body="""
        Building an audience in 2025 requires three key principles:

        1. Consistency: Post daily for at least 90 days
        2. Value-first: Always provide actionable insights
        3. Authenticity: Share your real experiences

        According to recent studies, 90% of creators quit within 3 months.
        However, those who persist see 300% increase in engagement after the 90-day mark.

        Here's a step-by-step process:
        1. Choose your niche
        2. Define 3-5 content pillars
        3. Create a content calendar
        4. Post daily
        5. Engage with every comment within 1 hour
        """,
        scraped_at="2025-11-22T12:00:00",
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)
    return content


class TestUltraLearningParser:
    """Test cases for UltraLearningParser"""

    def test_initialization_with_api_key(self):
        """Test parser initialization with API key."""
        parser = UltraLearningParser(api_key="test-key-123")
        assert parser.api_key == "test-key-123"
        assert parser.model == "claude-haiku-4-20250514"
        assert parser.max_tokens == 1000
        assert parser.batch_size == 100

    def test_initialization_without_api_key(self):
        """Test parser initialization fails without API key."""
        # Temporarily remove env var
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                UltraLearningParser()
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_create_extraction_prompt(self):
        """Test prompt creation."""
        parser = UltraLearningParser(api_key="test-key")
        prompt = parser._create_extraction_prompt("Test Title", "Test content body")

        assert "Test Title" in prompt
        assert "Test content body" in prompt
        assert "meta_subject" in prompt
        assert "concepts" in prompt
        assert "facts" in prompt
        assert "procedures" in prompt
        assert "JSON" in prompt

    def test_parse_claude_response_valid_json(self):
        """Test parsing valid JSON response."""
        parser = UltraLearningParser(api_key="test-key")

        response = json.dumps(
            {
                "meta_subject": "Content Marketing",
                "concepts": ["Consistency", "Value-first"],
                "facts": ["90% quit in 3 months"],
                "procedures": ["1. Choose niche", "2. Post daily"],
            }
        )

        result = parser._parse_claude_response(response)

        assert result["meta_subject"] == "Content Marketing"
        assert len(result["concepts"]) == 2
        assert len(result["facts"]) == 1
        assert len(result["procedures"]) == 2

    def test_parse_claude_response_with_markdown(self):
        """Test parsing JSON response wrapped in markdown."""
        parser = UltraLearningParser(api_key="test-key")

        response = """```json
{
  "meta_subject": "Audience Building",
  "concepts": ["Authenticity"],
  "facts": [],
  "procedures": []
}
```"""

        result = parser._parse_claude_response(response)

        assert result["meta_subject"] == "Audience Building"
        assert len(result["concepts"]) == 1
        assert result["facts"] == []

    def test_parse_claude_response_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        parser = UltraLearningParser(api_key="test-key")

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parser._parse_claude_response("Not valid JSON")

    def test_parse_claude_response_missing_fields(self):
        """Test parsing JSON with missing fields raises error."""
        parser = UltraLearningParser(api_key="test-key")

        response = json.dumps({"meta_subject": "Test", "concepts": []})

        with pytest.raises(ValueError, match="Missing required field"):
            parser._parse_claude_response(response)

    @patch("backend.services.ultra_learning_parser.anthropic.Anthropic")
    def test_parse_content_success(self, mock_anthropic):
        """Test successful content parsing."""
        # Mock Anthropic client response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "meta_subject": "Audience Building",
                        "concepts": ["Consistency", "Value-first"],
                        "facts": ["90% quit in 3 months"],
                        "procedures": ["1. Choose niche", "2. Post daily"],
                    }
                )
            )
        ]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=150)

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = UltraLearningParser(api_key="test-key")

        content_id = uuid4()
        result, input_tokens, output_tokens, processing_time = parser.parse_content(
            content_id=content_id,
            title="Test Title",
            body="Test body",
            link="https://example.com",
            platform="youtube",
            author_id="author123",
        )

        assert result["meta_subject"] == "Audience Building"
        assert len(result["concepts"]) == 2
        assert input_tokens == 500
        assert output_tokens == 150
        assert processing_time > 0

    def test_save_ultra_learning(self, test_db, sample_content):
        """Test saving ultra learning data to database."""
        parser = UltraLearningParser(api_key="test-key")

        parsed_data = {
            "content_id": str(sample_content.id),
            "title": sample_content.content_title,
            "link": sample_content.source_url,
            "platform": sample_content.platform,
            "author_id": sample_content.author_id,
            "meta_subject": "Audience Building",
            "concepts": ["Consistency", "Value-first"],
            "facts": ["90% quit in 3 months"],
            "procedures": ["1. Choose niche", "2. Post daily"],
        }

        result = parser.save_ultra_learning(test_db, parsed_data, input_tokens=500, output_tokens=150, processing_time_ms=1234)

        assert result.meta_subject == "Audience Building"
        assert len(result.concepts) == 2
        assert result.tokens_used == 650
        assert result.cost_cents >= 0
        assert result.processing_time_ms == 1234

        # Verify it was saved to database
        saved = test_db.query(UltraLearningORM).filter_by(content_id=sample_content.id).first()
        assert saved is not None
        assert saved.meta_subject == "Audience Building"

    def test_stats_tracking(self):
        """Test that stats are properly initialized."""
        parser = UltraLearningParser(api_key="test-key")

        assert parser.stats["items_processed"] == 0
        assert parser.stats["items_failed"] == 0
        assert parser.stats["total_input_tokens"] == 0
        assert parser.stats["concepts_extracted"] == 0
        assert parser.stats["subjects"] == {}

    def test_get_report(self):
        """Test report generation."""
        parser = UltraLearningParser(api_key="test-key")

        # Simulate some processing
        parser.stats["items_processed"] = 100
        parser.stats["items_failed"] = 5
        parser.stats["concepts_extracted"] = 300
        parser.stats["facts_extracted"] = 150
        parser.stats["procedures_extracted"] = 100
        parser.stats["total_input_tokens"] = 50000
        parser.stats["total_output_tokens"] = 15000
        parser.stats["total_cost_cents"] = 125
        parser.stats["subjects"] = {"Marketing": 30, "Branding": 25, "Sales": 20}
        parser.stats["total_processing_time_seconds"] = 123.45

        report = parser.get_report()

        assert "100" in report
        assert "5" in report
        assert "300" in report
        assert "Marketing" in report
        assert "$1.25" in report
        assert "123.45" in report


class TestUltraLearningIntegration:
    """Integration tests for Ultra Learning Parser"""

    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_real_parsing(self, test_db, sample_content):
        """Test real parsing with Anthropic API (requires API key)."""
        parser = UltraLearningParser(batch_size=1)

        result = parser.process_batch(test_db, limit=1)

        assert result["stats"]["items_processed"] >= 0
        assert "total_cost_cents" in result["stats"]

        # Check if content was parsed
        ultra_learning = test_db.query(UltraLearningORM).filter_by(content_id=sample_content.id).first()

        if ultra_learning:
            assert ultra_learning.meta_subject is not None
            assert isinstance(ultra_learning.concepts, list)
            assert isinstance(ultra_learning.facts, list)
            assert isinstance(ultra_learning.procedures, list)
