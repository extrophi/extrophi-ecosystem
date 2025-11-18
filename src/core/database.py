"""
Database connection and session management module.

This module provides async database connectivity using SQLAlchemy with asyncpg
driver for PostgreSQL. It includes support for connection pooling, multi-tenancy,
and proper session lifecycle management.

The module follows these patterns:
    - Async/await for all database operations
    - Connection pooling for performance
    - Automatic transaction management
    - Multi-tenant support with PostgreSQL schemas or RLS
    - Proper resource cleanup with context managers

Example:
    Basic usage with dependency injection:
        
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.database import get_session
        
        async def get_users(db: AsyncSession = Depends(get_session)):
            result = await db.execute(select(User))
            return result.scalars().all()

Note:
    The database URL must use the postgresql+asyncpg:// scheme for async support.
"""

# Standard library imports
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

# Third-party imports
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlmodel import SQLModel

# Local application imports
from src.core.config import settings
from src.core.diagnostics import DatabaseConnectionError

# Configure logging
logger = logging.getLogger(__name__)

# Global engine instance (initialized in init_db)
engine: Optional[AsyncEngine] = None

# Session factory (initialized in init_db)
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


async def init_db() -> None:
    """
    Initialize database connection and create tables.
    
    This function creates the async engine with proper connection pooling
    and initializes the session factory. It should be called once during
    application startup.
    
    Raises:
        Exception: If database connection fails
    """
    global engine, async_session_maker
    
    try:
        # Determine pool class based on environment
        pool_class = NullPool if settings.DEBUG else QueuePool
        
        # Get database settings and filter based on pool class
        db_settings = settings.get_database_settings()
        if pool_class == NullPool:
            # NullPool doesn't support pool_size or max_overflow
            db_settings = {k: v for k, v in db_settings.items() 
                          if k not in ['pool_size', 'max_overflow']}
        
        # Create async engine with optimized settings
        engine = create_async_engine(
            settings.DATABASE_URL,
            future=True,
            poolclass=pool_class,
            **db_settings
        )
        
        # Configure session factory
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,        # Require explicit commits
            autoflush=False          # Don't auto-flush before queries
        )
        
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Wrap in diagnostic error for better debugging
        if "connect" in str(e).lower() or "connection" in str(e).lower():
            raise DatabaseConnectionError(e, settings.DATABASE_URL)
        raise


async def close_db() -> None:
    """
    Close database connections and cleanup resources.
    
    This function should be called during application shutdown to properly
    close all database connections and free resources.
    """
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")
        engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic transaction management.
    
    This is the primary dependency for FastAPI endpoints that need database
    access. It automatically handles commits, rollbacks, and session cleanup.
    
    Yields:
        AsyncSession: Database session for the request
        
    Raises:
        Exception: If database operation fails
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.error("Database transaction rolled back due to error")
            raise
        finally:
            await session.close()


async def get_tenant_session(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with tenant context.
    
    This function provides a session configured for multi-tenant access.
    It can use PostgreSQL Row Level Security (RLS) or separate schemas
    depending on the deployment configuration.
    
    Args:
        tenant_id: Tenant identifier for context isolation
        
    Yields:
        AsyncSession: Tenant-scoped database session
        
    Raises:
        ValueError: If tenant_id is invalid
        Exception: If database operation fails
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    # Validate tenant ID
    if not tenant_id or not tenant_id.replace("-", "").isalnum():
        raise ValueError(f"Invalid tenant ID: {tenant_id}")
    
    async with async_session_maker() as session:
        try:
            # Set tenant context for RLS
            # This assumes PostgreSQL with RLS policies configured
            await session.execute(
                text("SET LOCAL app.current_tenant = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            
            # Log tenant context in debug mode
            if settings.DEBUG:
                logger.debug(f"Database session configured for tenant: {tenant_id}")
            
            yield session
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Tenant session error for {tenant_id}: {e}")
            raise
        finally:
            # Reset tenant context
            await session.execute(text("RESET app.current_tenant"))
            await session.close()


@asynccontextmanager
async def transactional_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a transactional session context manager.
    
    This provides explicit transaction control for complex operations
    that need to ensure atomicity across multiple database calls.
    
    Example:
        async with transactional_session() as session:
            user = User(name="John")
            session.add(user)
            # Transaction automatically commits on success
            # or rolls back on exception
    
    Yields:
        AsyncSession: Transactional database session
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        async with session.begin():
            yield session


async def check_database_health() -> dict[str, any]:
    """
    Check database health and connectivity.
    
    This function performs a simple health check query to verify
    database connectivity and responsiveness.
    
    Returns:
        Dictionary with health status and metrics
    """
    try:
        async with async_session_maker() as session:
            # Execute a simple query to check connectivity
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Get connection pool stats if available
            pool_stats = {}
            if hasattr(engine.pool, 'size'):
                pool_stats = {
                    "pool_size": engine.pool.size(),
                    "checked_out_connections": engine.pool.checked_out(),
                    "overflow": engine.pool.overflow(),
                    "total": engine.pool.total()
                }
            
            return {
                "status": "healthy",
                "connected": True,
                "pool_stats": pool_stats
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# Event listeners for connection lifecycle (optional)
@event.listens_for(QueuePool, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log new database connections."""
    logger.debug("New database connection established")


@event.listens_for(QueuePool, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkouts from pool."""
    logger.debug("Connection checked out from pool")


# Lifespan context manager (deprecated - use init_db/close_db instead)
@asynccontextmanager
async def lifespan(app):
    """
    Legacy lifespan context manager for backward compatibility.
    
    Deprecated: Use init_db() and close_db() directly in the main
    application lifespan handler instead.
    """
    await init_db()
    yield
    await close_db()