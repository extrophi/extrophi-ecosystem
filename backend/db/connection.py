"""Database connection and session management"""

import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://scraper:scraper_pass@postgres:5432/unified_scraper"
)


def get_engine():
    """
    Create SQLAlchemy engine with optimized connection pooling.

    Performance tuning:
    - pool_size: 20 (increased from 10 for higher concurrency)
    - max_overflow: 30 (increased from 20 for burst traffic)
    - pool_recycle: 3600 (recycle connections every hour)
    - pool_timeout: 30 (wait up to 30s for connection)
    - pool_pre_ping: True (verify connection health)
    """
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,  # Base pool size for concurrent requests
        max_overflow=30,  # Additional connections for burst traffic
        pool_timeout=30,  # Wait timeout for connection from pool
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Disable SQL logging for performance
        connect_args={
            "connect_timeout": 10,  # Connection timeout
            "options": "-c statement_timeout=30000"  # 30s query timeout
        }
    )
    return engine


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI endpoints to get database session"""
    engine = get_engine()
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def health_check() -> bool:
    """Check database connectivity"""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False


def init_db():
    """Initialize database tables"""
    from backend.db.models import Base

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
