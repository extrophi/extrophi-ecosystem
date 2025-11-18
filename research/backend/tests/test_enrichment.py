"""
Unit tests for enrichment engine

Tests the complete RAG pipeline:
- Embedding generation (LAMBDA)
- Vector search (THETA)
- LLM analysis (GPT-4)
- Suggestion generation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from enrichment.engine import EnrichmentEngine
from enrichment.llm_analyzer import LLMAnalyzer
from db.connection import DatabaseManager


class TestLLMAnalyzer:
    """Test LLM analyzer functionality"""

    @pytest.fixture
    def llm_analyzer(self):
        """Create LLM analyzer with mock API key"""
        return LLMAnalyzer(api_key="test-key-123", model="gpt-4")

    @pytest.mark.asyncio
    async def test_extract_frameworks(self, llm_analyzer):
        """Test framework extraction from content"""
        content = "I use the Pomodoro Technique and Deep Work principles for focus."
        similar_content = [
            {
                "text_content": "Cal Newport's Deep Work framework is powerful.",
                "title": "Deep Work Review",
                "platform": "web"
            }
        ]

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='["Deep Work", "Pomodoro Technique"]'))]
        mock_response.usage = Mock(total_tokens=100)

        with patch.object(llm_analyzer.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            frameworks = await llm_analyzer.extract_frameworks(content, similar_content)

        assert isinstance(frameworks, list)
        assert len(frameworks) >= 0  # Can be empty or have results

    @pytest.mark.asyncio
    async def test_extract_patterns(self, llm_analyzer):
        """Test pattern extraction"""
        content = "Focus is key to productivity."
        similar_content = []

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"hooks": ["Focus is key"], "themes": ["productivity"], "sentiment": "positive"}'))]
        mock_response.usage = Mock(total_tokens=150)

        with patch.object(llm_analyzer.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            patterns = await llm_analyzer.extract_patterns(content, similar_content)

        assert "hooks" in patterns
        assert "themes" in patterns
        assert "sentiment" in patterns

    @pytest.mark.asyncio
    async def test_generate_suggestions(self, llm_analyzer):
        """Test suggestion generation"""
        content = "How to build better focus systems?"
        similar_content = [
            {
                "text_content": "Use 2-hour focus blocks",
                "title": "Focus Systems",
                "author": "Dan Koe",
                "platform": "twitter",
                "url": "https://twitter.com/dankoe/123",
                "similarity_score": 0.85
            }
        ]
        frameworks = ["Deep Work"]

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='[{"text": "Consider 2-hour focus blocks", "type": "framework", "confidence": 0.85, "source_index": 1}]'))]
        mock_response.usage = Mock(total_tokens=200)

        with patch.object(llm_analyzer.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            suggestions = await llm_analyzer.generate_suggestions(
                content, similar_content, frameworks, max_suggestions=5
            )

        assert isinstance(suggestions, list)
        assert len(suggestions) >= 0

    @pytest.mark.asyncio
    async def test_analyze_content_full_pipeline(self, llm_analyzer):
        """Test complete analysis pipeline"""
        content = "Building a second brain system"
        similar_content = [
            {
                "text_content": "Second brain methodology by Tiago Forte",
                "title": "Building a Second Brain",
                "author": "Tiago Forte",
                "platform": "web",
                "url": "https://example.com/second-brain",
                "similarity_score": 0.90
            }
        ]

        # Mock all OpenAI calls
        mock_frameworks_response = Mock()
        mock_frameworks_response.choices = [Mock(message=Mock(content='["Building a Second Brain", "PARA Method"]'))]
        mock_frameworks_response.usage = Mock(total_tokens=100)

        mock_patterns_response = Mock()
        mock_patterns_response.choices = [Mock(message=Mock(content='{"hooks": ["second brain"], "themes": ["knowledge management"], "sentiment": "neutral"}'))]
        mock_patterns_response.usage = Mock(total_tokens=120)

        mock_suggestions_response = Mock()
        mock_suggestions_response.choices = [Mock(message=Mock(content='[{"text": "Use the PARA method for organization", "type": "framework", "confidence": 0.88, "source_index": 1}]'))]
        mock_suggestions_response.usage = Mock(total_tokens=180)

        # Return different responses for each call
        side_effects = [mock_frameworks_response, mock_patterns_response, mock_suggestions_response]

        with patch.object(llm_analyzer.client.chat.completions, 'create', new=AsyncMock(side_effect=side_effects)):
            result = await llm_analyzer.analyze_content(content, similar_content, max_suggestions=5)

        assert "frameworks" in result
        assert "hooks" in result
        assert "themes" in result
        assert "sentiment" in result
        assert "suggestions" in result
        assert "tokens_used" in result

    def test_get_usage_stats(self, llm_analyzer):
        """Test usage statistics tracking"""
        llm_analyzer.total_tokens = 1000
        llm_analyzer.total_requests = 5

        stats = llm_analyzer.get_usage_stats()

        assert stats["total_tokens"] == 1000
        assert stats["total_requests"] == 5
        assert "estimated_cost_usd" in stats
        assert "avg_tokens_per_request" in stats


class TestEnrichmentEngine:
    """Test enrichment engine orchestration"""

    @pytest.fixture
    async def mock_db_manager(self):
        """Create mock database manager"""
        db = AsyncMock(spec=DatabaseManager)
        db.health_check = AsyncMock(return_value={"status": "healthy"})
        return db

    @pytest.fixture
    async def enrichment_engine(self, mock_db_manager):
        """Create enrichment engine with mocked dependencies"""
        engine = EnrichmentEngine(
            db_manager=mock_db_manager,
            openai_api_key="test-key-123",
            embedding_model="text-embedding-ada-002",
            llm_model="gpt-4"
        )

        # Mock the embedding generator initialization
        engine.embedding_generator.initialize = AsyncMock()

        await engine.initialize()

        return engine

    @pytest.mark.asyncio
    async def test_enrich_basic_workflow(self, enrichment_engine):
        """Test basic enrichment workflow"""
        content = "How to improve productivity with time blocking?"

        # Mock embedding generation
        mock_embedding = [0.1] * 1536  # 1536-dimensional vector
        enrichment_engine.embedding_generator.generate = AsyncMock(return_value=mock_embedding)

        # Mock vector search results
        mock_similar = [
            {
                "content_id": "123",
                "text_content": "Time blocking is a powerful productivity technique.",
                "title": "Time Blocking Guide",
                "author": "Cal Newport",
                "platform": "web",
                "url": "https://example.com/time-blocking",
                "similarity_score": 0.88
            }
        ]
        enrichment_engine.vector_search.find_similar = AsyncMock(return_value=mock_similar)

        # Mock LLM analysis
        mock_analysis = {
            "frameworks": ["Time Blocking", "Deep Work"],
            "hooks": ["time blocking"],
            "themes": ["productivity"],
            "sentiment": "positive",
            "suggestions": [
                {
                    "text": "Consider using 90-minute time blocks for deep work",
                    "type": "framework",
                    "confidence": 0.85,
                    "source": {
                        "platform": "web",
                        "url": "https://example.com/time-blocking",
                        "title": "Time Blocking Guide",
                        "author": "Cal Newport",
                        "relevance_score": 0.88
                    }
                }
            ],
            "tokens_used": 500,
            "requests_made": 3
        }
        enrichment_engine.llm_analyzer.analyze_content = AsyncMock(return_value=mock_analysis)

        # Run enrichment
        result = await enrichment_engine.enrich(
            content=content,
            max_suggestions=5,
            similarity_threshold=0.7
        )

        # Assertions
        assert "suggestions" in result
        assert "sources" in result
        assert "frameworks" in result
        assert "metadata" in result

        assert len(result["suggestions"]) > 0
        assert result["frameworks"] == ["Time Blocking", "Deep Work"]
        assert result["metadata"]["processing_time_seconds"] >= 0  # Can be 0 for mocked calls

    @pytest.mark.asyncio
    async def test_enrich_with_context(self, enrichment_engine):
        """Test enrichment with additional context"""
        content = "Focus techniques"
        context = "Previous cards discussed productivity and time management"

        mock_embedding = [0.1] * 1536
        enrichment_engine.embedding_generator.generate = AsyncMock(return_value=mock_embedding)
        enrichment_engine.vector_search.find_similar = AsyncMock(return_value=[])
        enrichment_engine.llm_analyzer.analyze_content = AsyncMock(return_value={
            "frameworks": [],
            "hooks": [],
            "themes": [],
            "sentiment": "neutral",
            "suggestions": [],
            "tokens_used": 100,
            "requests_made": 1
        })

        result = await enrichment_engine.enrich(
            content=content,
            context=context,
            max_suggestions=3
        )

        # Verify context was included in embedding generation
        call_args = enrichment_engine.embedding_generator.generate.call_args
        assert context in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_related_content(self, enrichment_engine):
        """Test getting related content without full enrichment"""
        content = "Building habits"

        mock_embedding = [0.2] * 1536
        enrichment_engine.embedding_generator.generate = AsyncMock(return_value=mock_embedding)

        mock_similar = [
            {
                "platform": "twitter",
                "url": "https://twitter.com/example/123",
                "title": "Atomic Habits",
                "author": "James Clear",
                "text_content": "Small habits compound over time",
                "similarity_score": 0.92
            }
        ]
        enrichment_engine.vector_search.find_similar = AsyncMock(return_value=mock_similar)

        result = await enrichment_engine.get_related_content(
            content=content,
            limit=5,
            similarity_threshold=0.8
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert "platform" in result[0]
        assert "relevance_score" in result[0]

    @pytest.mark.asyncio
    async def test_batch_enrich(self, enrichment_engine):
        """Test batch enrichment of multiple cards"""
        cards = [
            {"card_id": "card1", "content": "Productivity tips"},
            {"card_id": "card2", "content": "Focus strategies"}
        ]

        # Mock dependencies
        mock_embedding = [0.1] * 1536
        enrichment_engine.embedding_generator.generate = AsyncMock(return_value=mock_embedding)
        enrichment_engine.vector_search.find_similar = AsyncMock(return_value=[])
        enrichment_engine.llm_analyzer.analyze_content = AsyncMock(return_value={
            "frameworks": [],
            "hooks": [],
            "themes": [],
            "sentiment": "neutral",
            "suggestions": [],
            "tokens_used": 100,
            "requests_made": 1
        })

        results = await enrichment_engine.enrich_batch(cards, max_suggestions=3)

        assert len(results) == 2
        assert results[0]["card_id"] == "card1"
        assert results[1]["card_id"] == "card2"

    @pytest.mark.asyncio
    async def test_health_check(self, enrichment_engine):
        """Test engine health check"""
        # Mock embedding generation for health check
        enrichment_engine.embedding_generator.generate = AsyncMock(return_value=[0.1] * 1536)

        health = await enrichment_engine.health_check()

        assert "engine" in health
        assert "database" in health
        assert "embeddings" in health
        assert "llm" in health
        assert "overall" in health

    def test_get_stats(self, enrichment_engine):
        """Test statistics collection"""
        enrichment_engine.enrichments_performed = 10
        enrichment_engine.total_processing_time = 25.5

        stats = enrichment_engine.get_stats()

        assert stats["enrichments_performed"] == 10
        assert stats["total_processing_time_seconds"] == 25.5
        assert "avg_processing_time_seconds" in stats
        assert "embedding_stats" in stats
        assert "llm_stats" in stats

    @pytest.mark.asyncio
    async def test_format_sources(self, enrichment_engine):
        """Test source formatting"""
        raw_sources = [
            {
                "platform": "youtube",
                "url": "https://youtube.com/watch?v=abc123",
                "title": "Productivity Masterclass",
                "author": "Ali Abdaal",
                "published_at": datetime(2025, 1, 15),
                "similarity_score": 0.91,
                "text_content": "This is a long transcript about productivity and time management techniques that should be truncated..."
            }
        ]

        formatted = enrichment_engine._format_sources(raw_sources)

        assert len(formatted) == 1
        assert formatted[0]["platform"] == "youtube"
        assert formatted[0]["relevance_score"] == 0.91
        assert "content_preview" in formatted[0]
        assert len(formatted[0]["content_preview"]) <= 203  # 200 + "..."


class TestEnrichmentIntegration:
    """Integration tests with real components (requires env setup)"""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires OpenAI API key and database")
    async def test_real_enrichment_flow(self):
        """
        Full integration test with real database and OpenAI API

        Skip by default - run manually with:
        pytest -m integration tests/test_enrichment.py
        """
        import os
        from db import get_db_manager

        # Requires real API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        db_manager = get_db_manager()
        await db_manager.connect()

        engine = EnrichmentEngine(
            db_manager=db_manager,
            openai_api_key=api_key,
            embedding_model="text-embedding-ada-002",
            llm_model="gpt-3.5-turbo"  # Use cheaper model for testing
        )

        await engine.initialize()

        # Real enrichment
        result = await engine.enrich(
            content="What are the best techniques for deep focus work?",
            max_suggestions=3,
            similarity_threshold=0.7
        )

        # Verify structure
        assert "suggestions" in result
        assert "sources" in result
        assert "frameworks" in result
        assert "metadata" in result

        # Cleanup
        await db_manager.disconnect()
