"""Database connection and session management for Research module"""

import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv(
    "RESEARCH_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://scraper:scraper_pass@localhost:5432/research_db")
)

def get_engine():
    """Create SQLAlchemy engine with connection pooling"""
    return create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )

def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI endpoints to get database session"""
    engine = get_engine()
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    try:
        yield db
    finally:
        db.close()

def health_check() -> dict:
    """Check database connectivity and pgvector extension"""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            result = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            )
            pgvector_exists = result.fetchone()[0]
            return {
                "status": "healthy",
                "connected": True,
                "pgvector_enabled": pgvector_exists,
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }

def init_db():
    """Initialize database tables from schema.sql"""
    import os.path
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    engine = get_engine()
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            for statement in schema_sql.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    connection.execute(text(statement))
            trans.commit()
            print("Database schema initialized successfully")
        except Exception as e:
            trans.rollback()
            raise Exception(f"Failed to initialize database: {e}")
