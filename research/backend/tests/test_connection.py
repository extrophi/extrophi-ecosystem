"""
Tests for database connection module
"""

import pytest

from db.connection import DatabaseManager


@pytest.mark.asyncio
async def test_connection_pool_creation(db_manager: DatabaseManager):
    """Test that connection pool is created successfully"""
    assert db_manager.pool is not None
    assert db_manager.pool.get_size() > 0


@pytest.mark.asyncio
async def test_connection_acquire(db_manager: DatabaseManager):
    """Test acquiring connection from pool"""
    async with db_manager.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1


@pytest.mark.asyncio
async def test_execute_query(db_manager: DatabaseManager):
    """Test executing a query"""
    result = await db_manager.fetchval("SELECT 1 + 1")
    assert result == 2


@pytest.mark.asyncio
async def test_fetch_multiple_rows(db_manager: DatabaseManager):
    """Test fetching multiple rows"""
    rows = await db_manager.fetch("SELECT * FROM sources LIMIT 10")
    assert isinstance(rows, list)


@pytest.mark.asyncio
async def test_health_check(db_manager: DatabaseManager):
    """Test database health check"""
    health = await db_manager.health_check()

    assert health["status"] == "healthy"
    assert "version" in health
    assert health["pgvector_enabled"] is True
    assert health["pool_size"] > 0


@pytest.mark.asyncio
async def test_pgvector_extension(db_manager: DatabaseManager):
    """Test that pgvector extension is installed"""
    result = await db_manager.fetchval(
        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
    )
    assert result is True
