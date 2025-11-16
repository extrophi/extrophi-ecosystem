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
    """Create SQLAlchemy engine with connection pooling"""
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
    )
    return engine


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI endpoints to get database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
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
