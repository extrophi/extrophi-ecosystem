"""
Database connection management with asyncpg connection pooling
"""

import logging
import os
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages PostgreSQL connection pooling with pgvector support

    Uses asyncpg for high-performance async database operations.
    Supports connection pooling for scalability.
    """

    def __init__(self):
        self.pool: Optional[Pool] = None
        self._connection_string: Optional[str] = None

    def get_connection_string(self) -> str:
        """
        Build PostgreSQL connection string from environment variables

        Environment variables:
        - DATABASE_URL: Full connection string (preferred)
        - DB_HOST: PostgreSQL host (default: localhost)
        - DB_PORT: PostgreSQL port (default: 5432)
        - DB_NAME: Database name (default: research_db)
        - DB_USER: Database user (default: postgres)
        - DB_PASSWORD: Database password (default: postgres)
        """
        # Check for full connection string first
        if database_url := os.getenv("DATABASE_URL"):
            return database_url

        # Build from individual components
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "research_db")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    async def connect(self, min_size: int = 10, max_size: int = 20) -> None:
        """
        Create connection pool

        Args:
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        if self.pool is not None:
            logger.warning("Connection pool already exists")
            return

        self._connection_string = self.get_connection_string()

        try:
            logger.info(f"Creating connection pool (min={min_size}, max={max_size})...")
            self.pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
                server_settings={
                    'application_name': 'research_backend',
                    'jit': 'off',  # Disable JIT for better cold-start performance
                }
            )
            logger.info("Database connection pool created successfully")

            # Verify pgvector extension
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                if result:
                    logger.info("pgvector extension verified")
                else:
                    logger.warning("pgvector extension not found - run schema.sql to install")

        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool is None:
            return

        try:
            logger.info("Closing connection pool...")
            await self.pool.close()
            self.pool = None
            logger.info("Connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")
            raise

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool (context manager)

        Usage:
            async with db_manager.acquire() as conn:
                result = await conn.fetch("SELECT * FROM contents")
        """
        if self.pool is None:
            raise RuntimeError("Connection pool not initialized - call connect() first")

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        """
        Execute a query without returning results

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Status string (e.g., 'INSERT 0 1')
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """
        Fetch multiple rows

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of records
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch single row

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """
        Fetch single value

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def health_check(self) -> dict:
        """
        Check database health

        Returns:
            Dict with health status and metrics
        """
        try:
            if self.pool is None:
                return {
                    "status": "disconnected",
                    "error": "Connection pool not initialized"
                }

            # Test query
            async with self.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                pgvector = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )

                # Get pool stats
                pool_size = self.pool.get_size()
                pool_idle = self.pool.get_idle_size()

                return {
                    "status": "healthy",
                    "version": version.split(',')[0],  # Shorten version string
                    "pgvector_enabled": pgvector,
                    "pool_size": pool_size,
                    "pool_idle": pool_idle,
                    "pool_active": pool_size - pool_idle,
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get global database manager instance (singleton)

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
