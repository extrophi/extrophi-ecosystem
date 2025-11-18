"""
Tests for CRUD operations
"""

from datetime import datetime
from uuid import UUID

import pytest

from db.crud import SourceCRUD, ContentCRUD, ScrapeJobCRUD


# ============================================================================
# SourceCRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_source(source_crud: SourceCRUD):
    """Test creating a source"""
    source_id = await source_crud.create(
        platform="twitter",
        url="https://twitter.com/test/status/123",
        title="Test Tweet",
        author="@testuser",
        metadata={"tweet_id": "123"}
    )

    assert isinstance(source_id, UUID)


@pytest.mark.asyncio
async def test_get_source_by_id(source_crud: SourceCRUD, sample_source):
    """Test getting source by ID"""
    source = await source_crud.get_by_id(sample_source)

    assert source is not None
    assert source["id"] == sample_source
    assert source["platform"] == "web"
    assert source["url"] == "https://test.example.com/article"


@pytest.mark.asyncio
async def test_get_source_by_url(source_crud: SourceCRUD, sample_source):
    """Test getting source by URL"""
    source = await source_crud.get_by_url("https://test.example.com/article")

    assert source is not None
    assert source["id"] == sample_source


@pytest.mark.asyncio
async def test_list_sources_by_platform(source_crud: SourceCRUD, sample_source):
    """Test listing sources by platform"""
    sources = await source_crud.list_by_platform("web", limit=10)

    assert isinstance(sources, list)
    assert len(sources) > 0
    assert all(s["platform"] == "web" for s in sources)


@pytest.mark.asyncio
async def test_update_source(source_crud: SourceCRUD, sample_source):
    """Test updating source"""
    success = await source_crud.update(
        sample_source,
        title="Updated Title",
        metadata={"updated": True}
    )

    assert success is True

    # Verify update
    source = await source_crud.get_by_id(sample_source)
    assert source["title"] == "Updated Title"
    assert source["metadata"]["updated"] is True


@pytest.mark.asyncio
async def test_count_sources_by_platform(source_crud: SourceCRUD, sample_source):
    """Test counting sources by platform"""
    counts = await source_crud.count_by_platform()

    assert isinstance(counts, list)
    assert len(counts) > 0
    assert all("platform" in c and "count" in c for c in counts)


# ============================================================================
# ContentCRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_content(content_crud: ContentCRUD, sample_source):
    """Test creating content"""
    content_id = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="This is test content about AI and machine learning.",
        metadata={"language": "en"}
    )

    assert isinstance(content_id, UUID)


@pytest.mark.asyncio
async def test_create_content_with_embedding(content_crud: ContentCRUD, sample_source):
    """Test creating content with embedding"""
    # Create a dummy 1536-dimension embedding (all zeros for testing)
    embedding = [0.0] * 1536

    content_id = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="Test content with embedding",
        embedding=embedding
    )

    assert isinstance(content_id, UUID)

    # Verify embedding was stored
    content = await content_crud.get_by_id(content_id)
    assert content is not None
    assert content["embedding"] is not None


@pytest.mark.asyncio
async def test_get_content_by_id(content_crud: ContentCRUD, sample_content):
    """Test getting content by ID"""
    content = await content_crud.get_by_id(sample_content)

    assert content is not None
    assert content["id"] == sample_content
    assert content["content_type"] == "text"


@pytest.mark.asyncio
async def test_list_content_by_source(content_crud: ContentCRUD, sample_source, sample_content):
    """Test listing content by source"""
    contents = await content_crud.list_by_source(sample_source, limit=10)

    assert isinstance(contents, list)
    assert len(contents) > 0
    assert all(c["source_id"] == sample_source for c in contents)


@pytest.mark.asyncio
async def test_update_embedding(content_crud: ContentCRUD, sample_content):
    """Test updating content embedding"""
    # Create a dummy embedding
    embedding = [0.1] * 1536

    success = await content_crud.update_embedding(sample_content, embedding)
    assert success is True

    # Verify update
    content = await content_crud.get_by_id(sample_content)
    assert content["embedding"] is not None


@pytest.mark.asyncio
async def test_count_with_embeddings(content_crud: ContentCRUD, sample_content):
    """Test counting contents with embeddings"""
    count = await content_crud.count_with_embeddings()
    assert isinstance(count, int)
    assert count >= 0


@pytest.mark.asyncio
async def test_count_without_embeddings(content_crud: ContentCRUD, sample_content):
    """Test counting contents without embeddings"""
    count = await content_crud.count_without_embeddings()
    assert isinstance(count, int)
    assert count >= 0


# ============================================================================
# ScrapeJobCRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_job(job_crud: ScrapeJobCRUD):
    """Test creating scrape job"""
    job_id = await job_crud.create(
        url="https://example.com/test",
        platform="web",
        depth=2,
        extract_embeddings=True
    )

    assert isinstance(job_id, UUID)


@pytest.mark.asyncio
async def test_get_job_by_id(job_crud: ScrapeJobCRUD):
    """Test getting job by ID"""
    job_id = await job_crud.create(
        url="https://example.com/test2",
        platform="web"
    )

    job = await job_crud.get_by_id(job_id)

    assert job is not None
    assert job["id"] == job_id
    assert job["status"] == "pending"


@pytest.mark.asyncio
async def test_update_job_status(job_crud: ScrapeJobCRUD):
    """Test updating job status"""
    job_id = await job_crud.create(
        url="https://example.com/test3",
        platform="web"
    )

    # Start processing
    success = await job_crud.update_status(job_id, "processing")
    assert success is True

    job = await job_crud.get_by_id(job_id)
    assert job["status"] == "processing"
    assert job["started_at"] is not None

    # Complete job
    success = await job_crud.update_status(
        job_id,
        "completed",
        items_scraped=10
    )
    assert success is True

    job = await job_crud.get_by_id(job_id)
    assert job["status"] == "completed"
    assert job["completed_at"] is not None
    assert job["items_scraped"] == 10


@pytest.mark.asyncio
async def test_update_job_with_error(job_crud: ScrapeJobCRUD):
    """Test updating job with error"""
    job_id = await job_crud.create(
        url="https://example.com/test4",
        platform="web"
    )

    success = await job_crud.update_status(
        job_id,
        "failed",
        error_message="Test error message"
    )
    assert success is True

    job = await job_crud.get_by_id(job_id)
    assert job["status"] == "failed"
    assert job["error_message"] == "Test error message"


@pytest.mark.asyncio
async def test_list_jobs_by_status(job_crud: ScrapeJobCRUD):
    """Test listing jobs by status"""
    # Create a few test jobs
    await job_crud.create(url="https://example.com/pending1", platform="web")
    await job_crud.create(url="https://example.com/pending2", platform="web")

    jobs = await job_crud.list_by_status("pending", limit=10)

    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert all(j["status"] == "pending" for j in jobs)


@pytest.mark.asyncio
async def test_list_pending_jobs(job_crud: ScrapeJobCRUD):
    """Test listing pending jobs"""
    await job_crud.create(url="https://example.com/pending3", platform="web")

    jobs = await job_crud.list_pending(limit=5)

    assert isinstance(jobs, list)
    assert all(j["status"] == "pending" for j in jobs)


@pytest.mark.asyncio
async def test_get_job_statistics(job_crud: ScrapeJobCRUD):
    """Test getting job statistics"""
    stats = await job_crud.get_statistics()

    assert isinstance(stats, dict)
    # Should have at least 'pending' status from previous tests
    if 'pending' in stats:
        assert 'count' in stats['pending']
