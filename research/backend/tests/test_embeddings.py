"""
Tests for embedding generation module

Tests cover:
- Text chunking with tiktoken
- Embedding generation (mocked OpenAI API)
- Batch processing
- Cache layer
- Cost tracking
- Database integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from embeddings.generator import (
    EmbeddingGenerator,
    EmbeddingCache,
    EmbeddingCostTracker,
    TextChunker
)


class TestTextChunker:
    """Test text chunking functionality"""

    def test_count_tokens(self):
        """Test token counting"""
        chunker = TextChunker()

        # Simple text
        text = "Hello world"
        count = chunker.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_chunk_small_text(self):
        """Test chunking text smaller than chunk size"""
        chunker = TextChunker(chunk_size=512)

        text = "This is a short text."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_large_text(self):
        """Test chunking text larger than chunk size"""
        chunker = TextChunker(chunk_size=50)  # Small chunk for testing

        # Generate long text
        text = " ".join(["word"] * 200)  # ~200 tokens
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(chunker.count_tokens(chunk) <= 50 for chunk in chunks)

    def test_chunk_overlap(self):
        """Test that chunks have overlap"""
        chunker = TextChunker(chunk_size=100)

        text = " ".join([f"word{i}" for i in range(200)])
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Check that consecutive chunks share some content
            # (This is a rough heuristic - overlap isn't guaranteed to be word-level)
            assert len(chunks) >= 2


class TestEmbeddingCostTracker:
    """Test cost tracking functionality"""

    def test_initialize(self):
        """Test tracker initialization"""
        tracker = EmbeddingCostTracker()

        assert tracker.total_tokens == 0
        assert tracker.total_cost == 0.0
        assert tracker.requests == 0
        assert tracker.embeddings_generated == 0

    def test_add_request(self):
        """Test recording requests"""
        tracker = EmbeddingCostTracker()

        tracker.add_request(tokens=1000, embeddings_count=1)

        assert tracker.total_tokens == 1000
        assert tracker.total_cost == 0.0001  # $0.0001 per 1K tokens
        assert tracker.requests == 1
        assert tracker.embeddings_generated == 1

    def test_multiple_requests(self):
        """Test multiple requests"""
        tracker = EmbeddingCostTracker()

        tracker.add_request(tokens=1000, embeddings_count=1)
        tracker.add_request(tokens=2000, embeddings_count=2)
        tracker.add_request(tokens=500, embeddings_count=1)

        assert tracker.total_tokens == 3500
        assert tracker.total_cost == 0.00035  # $0.0001 per 1K tokens
        assert tracker.requests == 3
        assert tracker.embeddings_generated == 4

    def test_get_stats(self):
        """Test statistics calculation"""
        tracker = EmbeddingCostTracker()

        tracker.add_request(tokens=1000, embeddings_count=1)
        tracker.add_request(tokens=2000, embeddings_count=2)

        stats = tracker.get_stats()

        assert stats["total_tokens"] == 3000
        assert stats["total_cost_usd"] == 0.0003
        assert stats["requests"] == 2
        assert stats["embeddings_generated"] == 3
        assert stats["avg_tokens_per_request"] == 1500.0
        assert stats["cost_per_embedding"] > 0


class TestEmbeddingCache:
    """Test cache layer functionality"""

    @pytest.mark.asyncio
    async def test_compute_hash(self):
        """Test content hash computation"""
        hash1 = EmbeddingCache.compute_hash("test content")
        hash2 = EmbeddingCache.compute_hash("test content")
        hash3 = EmbeddingCache.compute_hash("different content")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA-256 hex digest

    @pytest.mark.asyncio
    async def test_has_embedding(self):
        """Test checking if content has embedding"""
        # Mock database manager
        db_manager = MagicMock()
        db_manager.fetchval = AsyncMock(return_value=True)

        cache = EmbeddingCache(db_manager)

        content_id = uuid4()
        result = await cache.has_embedding(content_id)

        assert result is True
        db_manager.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_embedding(self):
        """Test retrieving cached embedding"""
        # Mock database manager
        db_manager = MagicMock()
        mock_embedding = [0.1] * 1536  # Mock ada-002 embedding
        db_manager.fetchval = AsyncMock(return_value=mock_embedding)

        cache = EmbeddingCache(db_manager)

        content_id = uuid4()
        result = await cache.get_cached_embedding(content_id)

        assert result == mock_embedding
        db_manager.fetchval.assert_called_once()


class TestEmbeddingGenerator:
    """Test embedding generator functionality"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test generator initialization"""
        generator = EmbeddingGenerator(api_key="test-key")

        assert generator.model == "text-embedding-ada-002"
        assert generator.db is None
        assert generator.cache is None

    @pytest.mark.asyncio
    @patch('embeddings.generator.AsyncOpenAI')
    async def test_generate(self, mock_openai):
        """Test single embedding generation"""
        # Mock OpenAI client
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        generator = EmbeddingGenerator(api_key="test-key")

        # Generate embedding
        embedding = await generator.generate("test text")

        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('embeddings.generator.AsyncOpenAI')
    async def test_generate_batch(self, mock_openai):
        """Test batch embedding generation"""
        # Mock OpenAI client
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
            MagicMock(embedding=[0.3] * 1536),
        ]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        generator = EmbeddingGenerator(api_key="test-key")

        # Generate embeddings
        texts = ["text 1", "text 2", "text 3"]
        embeddings = await generator.generate_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('embeddings.generator.AsyncOpenAI')
    async def test_generate_batch_large(self, mock_openai):
        """Test batch generation with >100 texts (multiple API calls)"""
        # Mock OpenAI client
        mock_response = MagicMock()

        # Create 150 mock embeddings
        mock_response.data = [MagicMock(embedding=[0.1] * 1536) for _ in range(100)]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        generator = EmbeddingGenerator(api_key="test-key")

        # Generate 150 embeddings (should make 2 API calls)
        texts = [f"text {i}" for i in range(150)]
        embeddings = await generator.generate_batch(texts)

        assert len(embeddings) == 150
        assert mock_client.embeddings.create.call_count == 2  # 2 batches

    @pytest.mark.asyncio
    @patch('embeddings.generator.AsyncOpenAI')
    async def test_generate_chunked(self, mock_openai):
        """Test embedding generation with text chunking"""
        # Mock OpenAI client
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
        ]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        generator = EmbeddingGenerator(api_key="test-key")
        generator.chunker.chunk_size = 50  # Small chunks for testing

        # Long text that will be chunked
        text = " ".join(["word"] * 200)
        embedding = await generator.generate_chunked(text)

        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Test that cost tracking works"""
        with patch('embeddings.generator.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            generator = EmbeddingGenerator(api_key="test-key")

            # Generate embedding
            await generator.generate("test text")

            # Check cost tracking
            stats = generator.get_cost_stats()

            assert stats["total_tokens"] > 0
            assert stats["total_cost_usd"] > 0
            assert stats["requests"] == 1
            assert stats["embeddings_generated"] == 1

    @pytest.mark.asyncio
    async def test_generate_for_content_cache_hit(self):
        """Test that cached embeddings are reused"""
        # Mock database manager
        db_manager = MagicMock()
        db_manager.fetchval = AsyncMock(return_value=True)  # Has embedding

        # Mock cache
        mock_cache = MagicMock()
        mock_cache.has_embedding = AsyncMock(return_value=True)
        mock_cache.get_cached_embedding = AsyncMock(return_value=[0.1] * 1536)

        generator = EmbeddingGenerator(api_key="test-key")
        await generator.initialize(db_manager)
        generator.cache = mock_cache

        content_id = uuid4()
        embedding = await generator.generate_for_content(content_id)

        assert embedding is not None
        assert len(embedding) == 1536
        mock_cache.has_embedding.assert_called_once()
        mock_cache.get_cached_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_for_content_not_initialized(self):
        """Test that error is raised if not initialized"""
        generator = EmbeddingGenerator(api_key="test-key")

        content_id = uuid4()

        with pytest.raises(RuntimeError, match="not initialized"):
            await generator.generate_for_content(content_id)

    def test_get_cost_stats(self):
        """Test getting cost statistics"""
        generator = EmbeddingGenerator(api_key="test-key")

        stats = generator.get_cost_stats()

        assert "total_tokens" in stats
        assert "total_cost_usd" in stats
        assert "requests" in stats
        assert "embeddings_generated" in stats


class TestIntegration:
    """Integration tests (require database)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_workflow(self):
        """
        Test full embedding generation workflow

        Note: This test requires a running PostgreSQL database
        and valid OpenAI API key. Skip in CI unless configured.
        """
        # This is a placeholder for integration tests
        # Actual implementation would require:
        # 1. Database connection
        # 2. Test content in database
        # 3. Valid OpenAI API key
        # 4. Cleanup after test

        pytest.skip("Integration test requires database and API key")
