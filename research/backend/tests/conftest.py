"""
Pytest configuration and fixtures for database tests
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from db.connection import DatabaseManager
from db.crud import SourceCRUD, ContentCRUD, ScrapeJobCRUD
from db.search import VectorSearch

# Load environment variables
load_dotenv()

# Use test database
os.environ["DB_NAME"] = os.getenv("TEST_DB_NAME", "research_db_test")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """
    Create database manager for tests

    Uses a test database to avoid affecting production data.
    """
    manager = DatabaseManager()

    # Connect to database
    await manager.connect(min_size=2, max_size=5)

    yield manager

    # Cleanup
    await manager.disconnect()


@pytest_asyncio.fixture(scope="function")
async def source_crud(db_manager: DatabaseManager) -> SourceCRUD:
    """Create SourceCRUD instance"""
    return SourceCRUD(db_manager)


@pytest_asyncio.fixture(scope="function")
async def content_crud(db_manager: DatabaseManager) -> ContentCRUD:
    """Create ContentCRUD instance"""
    return ContentCRUD(db_manager)


@pytest_asyncio.fixture(scope="function")
async def job_crud(db_manager: DatabaseManager) -> ScrapeJobCRUD:
    """Create ScrapeJobCRUD instance"""
    return ScrapeJobCRUD(db_manager)


@pytest_asyncio.fixture(scope="function")
async def vector_search(db_manager: DatabaseManager) -> VectorSearch:
    """Create VectorSearch instance"""
    return VectorSearch(db_manager)


@pytest_asyncio.fixture(scope="function")
async def sample_source(source_crud: SourceCRUD):
    """Create sample source for tests"""
    source_id = await source_crud.create(
        platform="web",
        url="https://test.example.com/article",
        title="Test Article",
        author="Test Author",
    )
    return source_id


@pytest_asyncio.fixture(scope="function")
async def sample_content(content_crud: ContentCRUD, sample_source):
    """Create sample content for tests"""
    content_id = await content_crud.create(
        source_id=sample_source,
        content_type="text",
        text_content="This is a test article about machine learning and AI.",
    )
    return content_id
