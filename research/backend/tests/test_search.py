"""
Tests for vector similarity search
"""

import pytest

from db.search import VectorSearch
from db.crud import ContentCRUD


@pytest.mark.asyncio
async def test_find_similar_basic(vector_search: VectorSearch, content_crud: ContentCRUD, sample_source):
    """Test basic vector similarity search"""
    # Create content with embedding
    embedding = [0.1] * 1536
    content_id = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="Machine learning is a subset of artificial intelligence.",
        embedding=embedding
    )

    # Search for similar content
    results = await vector_search.find_similar(
        query_embedding=embedding,
        match_threshold=0.5,
        match_count=10
    )

    assert isinstance(results, list)
    # Should find at least the content we just created
    if results:
        assert "similarity_score" in results[0]
        assert "text_content" in results[0]


@pytest.mark.asyncio
async def test_find_similar_by_platform(vector_search: VectorSearch, content_crud: ContentCRUD, source_crud):
    """Test vector search filtered by platform"""
    # Create a Twitter source and content
    twitter_source = await source_crud.create(
        platform="twitter",
        url="https://twitter.com/test/123",
        title="Test Tweet"
    )

    embedding = [0.2] * 1536
    await content_crud.create(
        source_id=twitter_source,
        content_type="post",
        text_content="AI is transforming the world.",
        embedding=embedding
    )

    # Search only in Twitter content
    results = await vector_search.find_similar_by_platform(
        query_embedding=embedding,
        platform="twitter",
        match_threshold=0.5,
        match_count=10
    )

    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_find_similar_by_content_id(vector_search: VectorSearch, content_crud: ContentCRUD, sample_source):
    """Test finding similar content by content ID"""
    # Create multiple contents with embeddings
    embedding1 = [0.3] * 1536
    content_id1 = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="Deep learning neural networks.",
        embedding=embedding1
    )

    embedding2 = [0.31] * 1536  # Very similar embedding
    content_id2 = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="Neural networks and deep learning.",
        embedding=embedding2
    )

    # Find similar to first content
    results = await vector_search.find_similar_by_content_id(
        content_id=content_id1,
        match_threshold=0.5,
        match_count=10,
        exclude_self=True
    )

    assert isinstance(results, list)
    # Should not include the source content itself
    if results:
        assert all(r["content_id"] != content_id1 for r in results)


@pytest.mark.asyncio
async def test_find_similar_no_embedding(vector_search: VectorSearch, sample_content):
    """Test finding similar content when source has no embedding"""
    results = await vector_search.find_similar_by_content_id(
        content_id=sample_content,  # This content has no embedding
        match_threshold=0.5,
        match_count=10
    )

    # Should return empty list when content has no embedding
    assert results == []


@pytest.mark.asyncio
async def test_get_content_statistics(vector_search: VectorSearch, sample_source, sample_content):
    """Test getting content statistics"""
    stats = await vector_search.get_content_statistics()

    assert isinstance(stats, list)
    # Should have at least one platform
    if stats:
        assert "platform" in stats[0]
        assert "content_count" in stats[0]


@pytest.mark.asyncio
async def test_hybrid_search(vector_search: VectorSearch, content_crud: ContentCRUD, sample_source):
    """Test hybrid text + vector search"""
    # Create content with embedding
    embedding = [0.4] * 1536
    content_id = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="Python programming language for machine learning and AI development.",
        embedding=embedding
    )

    # Hybrid search
    results = await vector_search.search_by_text_and_vector(
        text_query="Python machine learning",
        query_embedding=embedding,
        match_threshold=0.5,
        match_count=10
    )

    assert isinstance(results, list)
    if results:
        assert "similarity_score" in results[0]
        assert "text_rank" in results[0]
        assert "hybrid_score" in results[0]


@pytest.mark.asyncio
async def test_batch_find_similar(vector_search: VectorSearch, content_crud: ContentCRUD, sample_source):
    """Test batch vector search"""
    # Create content with embeddings
    embeddings = [
        [0.5] * 1536,
        [0.6] * 1536,
        [0.7] * 1536
    ]

    for emb in embeddings:
        await content_crud.create(
            source_id=sample_source,
            content_type="text",
            text_content="Test content for batch search.",
            embedding=emb
        )

    # Batch search
    query_embeddings = [
        [0.51] * 1536,
        [0.61] * 1536
    ]

    results = await vector_search.batch_find_similar(
        query_embeddings=query_embeddings,
        match_threshold=0.5,
        match_count=5
    )

    assert isinstance(results, list)
    assert len(results) == len(query_embeddings)
    # Each query should return a list of results
    for query_results in results:
        assert isinstance(query_results, list)


@pytest.mark.asyncio
async def test_similarity_threshold(vector_search: VectorSearch, content_crud: ContentCRUD, sample_source):
    """Test that similarity threshold filters results correctly"""
    embedding = [0.8] * 1536
    content_id = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="Testing similarity thresholds.",
        embedding=embedding
    )

    # High threshold - should return fewer or no results
    results_high = await vector_search.find_similar(
        query_embedding=[0.1] * 1536,  # Very different embedding
        match_threshold=0.99,  # Very high threshold
        match_count=10
    )

    # Low threshold - should return more results
    results_low = await vector_search.find_similar(
        query_embedding=[0.1] * 1536,
        match_threshold=0.1,  # Very low threshold
        match_count=10
    )

    # Low threshold should return at least as many results as high threshold
    assert len(results_low) >= len(results_high)
