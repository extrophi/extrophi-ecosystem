# AGENT ALPHA: PostgreSQL + pgvector Database Foundation

**Priority**: CRITICAL (Blocks all other agents)
**Estimated Time**: 45-60 minutes
**Dependencies**: None (first agent)
**Blocks**: Agent Beta, Gamma, Delta, Epsilon

---

## MISSION

Set up the complete PostgreSQL 16 + pgvector database foundation for IAC-032 Unified Scraper. This includes connection pooling, SQLAlchemy ORM models, Pydantic v2 schemas, and the full database schema with vector embeddings support.

**Success = Other agents can immediately connect and start building scrapers/APIs on top of your foundation.**

---

## CONTEXT

You are building the database layer for a **multi-platform content intelligence engine** that:
- Scrapes Twitter, YouTube, Reddit, Amazon, and Web content
- Stores content with OpenAI embeddings (1536 dimensions) for semantic search
- Analyzes content for copywriting frameworks (AIDA, PAS, BAB, PASTOR)
- Detects cross-platform content patterns
- Powers RAG (Retrieval Augmented Generation) queries

This is the **foundation layer** - every other component depends on you.

---

## ENVIRONMENT SETUP

### Prerequisites (Must verify these exist)

```bash
# Check PostgreSQL 16 is installed
psql --version  # Should show 16.x

# Check pgvector extension is available
psql -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Check UV is installed
uv --version

# Create project database
createdb unified_scraper_dev
```

If PostgreSQL 16 or pgvector is not installed:

```bash
# macOS with Homebrew (only for database tools, NOT Python)
brew install postgresql@16
brew install pgvector

# Start PostgreSQL
brew services start postgresql@16

# Create database user (if needed)
createuser -s $(whoami)
```

---

## FILES TO CREATE

### Directory Structure

```
/Users/kjd/01-projects/IAC-032-unified-scraper/
├── backend/
│   ├── __init__.py
│   ├── pyproject.toml
│   └── db/
│       ├── __init__.py
│       ├── connection.py
│       ├── models.py
│       └── schema.sql
```

---

## FILE 1: backend/pyproject.toml

**Purpose**: UV package manager configuration with all database dependencies

```toml
[project]
name = "unified-scraper-backend"
version = "0.1.0"
description = "Multi-platform content intelligence engine"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # Database
    "sqlalchemy>=2.0.23",
    "psycopg2-binary>=2.9.9",
    "pgvector>=0.2.4",
    "alembic>=1.13.1",

    # Validation
    "pydantic>=2.5.2",
    "pydantic-settings>=2.1.0",

    # Async
    "asyncpg>=0.29.0",

    # Utilities
    "python-dotenv>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.2",
]
```

---

## FILE 2: backend/__init__.py

**Purpose**: Package initialization

```python
"""
IAC-032 Unified Scraper Backend

Multi-platform content intelligence engine with RAG capabilities.
"""

__version__ = "0.1.0"
```

---

## FILE 3: backend/db/__init__.py

**Purpose**: Database package exports

```python
"""
Database layer for Unified Scraper.

Exports:
- Database: Connection manager with pooling
- Models: SQLAlchemy ORM models
- Schemas: Pydantic v2 validation schemas
"""

from backend.db.connection import Database, get_db
from backend.db.models import (
    # ORM Models
    ContentORM,
    AuthorORM,
    PatternORM,
    FrameworkORM,

    # Pydantic Schemas
    ContentCreate,
    ContentRead,
    ContentUpdate,
    AuthorCreate,
    AuthorRead,
    PatternCreate,
    PatternRead,
    FrameworkCreate,
    FrameworkRead,

    # Enums
    Platform,
    FrameworkType,
    PatternType,
)

__all__ = [
    "Database",
    "get_db",
    "ContentORM",
    "AuthorORM",
    "PatternORM",
    "FrameworkORM",
    "ContentCreate",
    "ContentRead",
    "ContentUpdate",
    "AuthorCreate",
    "AuthorRead",
    "PatternCreate",
    "PatternRead",
    "FrameworkCreate",
    "FrameworkRead",
    "Platform",
    "FrameworkType",
    "PatternType",
]
```

---

## FILE 4: backend/db/connection.py

**Purpose**: Database connection manager with connection pooling

```python
"""
Database connection manager with SQLAlchemy QueuePool.

Features:
- Connection pooling (20 connections, 10 overflow)
- Automatic reconnection
- Context manager support
- Singleton pattern for app-wide usage
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()


class Database:
    """
    Database connection manager with connection pooling.

    Usage:
        db = Database()
        with db.session() as session:
            result = session.execute(text("SELECT 1"))
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern - one connection pool per app."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize database connection pool."""
        if self._initialized:
            return

        self._initialized = True

        # Build connection string
        self.database_url = self._build_connection_string()

        # Create engine with QueuePool
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=20,           # Base pool size
            max_overflow=10,        # Allow 10 extra connections
            pool_timeout=30,        # Wait 30s for connection
            pool_recycle=1800,      # Recycle connections every 30min
            pool_pre_ping=True,     # Verify connections before use
            echo=False,             # Set True for SQL logging
        )

        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        # Register connection event handlers
        self._register_events()

    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment."""
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER", os.getenv("USER", "postgres"))
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "unified_scraper_dev")

        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"postgresql://{user}@{host}:{port}/{database}"

    def _register_events(self):
        """Register SQLAlchemy event handlers."""

        @event.listens_for(self.engine, "connect")
        def set_search_path(dbapi_conn, connection_record):
            """Set search path on new connections."""
            cursor = dbapi_conn.cursor()
            cursor.execute("SET search_path TO public")
            cursor.close()

        @event.listens_for(self.engine, "checkout")
        def ping_connection(dbapi_conn, connection_record, connection_proxy):
            """Verify connection is alive before checkout."""
            cursor = dbapi_conn.cursor()
            try:
                cursor.execute("SELECT 1")
            except:
                # Raise to force pool to reconnect
                raise
            finally:
                cursor.close()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db.session() as session:
                content = session.query(ContentORM).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_sql_file(self, file_path: str) -> None:
        """
        Execute SQL file (for schema setup).

        Args:
            file_path: Path to .sql file
        """
        with open(file_path, "r") as f:
            sql = f.read()

        with self.engine.connect() as conn:
            # Split by semicolon and execute each statement
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
            conn.commit()

    def health_check(self) -> dict:
        """
        Check database connectivity and pool status.

        Returns:
            dict with connection status and pool stats
        """
        try:
            with self.session() as session:
                # Test basic query
                result = session.execute(text("SELECT version()")).scalar()

                # Check pgvector extension
                pgvector = session.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                ).scalar()

            return {
                "status": "healthy",
                "postgresql_version": result,
                "pgvector_version": pgvector,
                "pool_size": self.engine.pool.size(),
                "pool_checkedin": self.engine.pool.checkedin(),
                "pool_checkedout": self.engine.pool.checkedout(),
                "pool_overflow": self.engine.pool.overflow(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def close(self):
        """Close all connections in the pool."""
        self.engine.dispose()
        Database._instance = None
        self._initialized = False


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage in FastAPI:
        @app.get("/contents")
        def get_contents(db: Session = Depends(get_db)):
            return db.query(ContentORM).all()
    """
    database = Database()
    with database.session() as session:
        yield session
```

---

## FILE 5: backend/db/models.py

**Purpose**: SQLAlchemy ORM models + Pydantic v2 schemas

```python
"""
Database models and Pydantic schemas for Unified Scraper.

Models:
- ContentORM: Scraped content with embeddings
- AuthorORM: Content authors (Twitter handles, YouTube channels, etc.)
- PatternORM: Cross-platform content patterns
- FrameworkORM: Copywriting framework analysis

Schemas (Pydantic v2):
- Create/Read/Update schemas for each model
- Proper JSON serialization with vector support
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# SQLAlchemy Base
Base = declarative_base()


# ===== ENUMS =====

class Platform(str, Enum):
    """Supported content platforms."""
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    AMAZON = "amazon"
    WEB = "web"


class FrameworkType(str, Enum):
    """Copywriting framework types."""
    AIDA = "aida"           # Attention, Interest, Desire, Action
    PAS = "pas"             # Problem, Agitate, Solution
    BAB = "bab"             # Before, After, Bridge
    PASTOR = "pastor"       # Problem, Amplify, Story, Transformation, Offer, Response
    HOOK = "hook"           # Curiosity, specificity, benefit-driven
    OTHER = "other"


class PatternType(str, Enum):
    """Content pattern types."""
    CROSS_PLATFORM = "cross_platform"   # Same content adapted across platforms
    SERIAL = "serial"                   # Content series (part 1, part 2, etc.)
    RESPONSE = "response"               # Response to other content
    VIRAL = "viral"                     # High engagement pattern
    AUTHORITY = "authority"             # Establishes expertise


# ===== ORM MODELS =====

class AuthorORM(Base):
    """Content author (Twitter user, YouTube channel, etc.)"""
    __tablename__ = "authors"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    platform = Column(String(50), nullable=False)
    platform_id = Column(String(255), nullable=False)  # Twitter handle, YouTube channel ID
    display_name = Column(String(255))
    bio = Column(Text)
    follower_count = Column(Integer)
    following_count = Column(Integer)
    total_content = Column(Integer, default=0)
    avg_engagement = Column(Float, default=0.0)
    authority_score = Column(Float, default=0.0)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    contents = relationship("ContentORM", back_populates="author")

    # Indexes
    __table_args__ = (
        Index("idx_authors_platform_id", "platform", "platform_id", unique=True),
        Index("idx_authors_authority", "authority_score"),
    )


class ContentORM(Base):
    """Scraped content with embeddings for semantic search."""
    __tablename__ = "contents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    platform = Column(String(50), nullable=False)
    source_url = Column(Text, unique=True, nullable=False)

    # Author relationship
    author_id = Column(PGUUID(as_uuid=True), ForeignKey("authors.id"))

    # Content data
    title = Column(Text)
    body = Column(Text, nullable=False)
    content_type = Column(String(50))  # tweet, video, post, review, article
    published_at = Column(DateTime)

    # Metrics (platform-specific)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)

    # LLM Analysis
    frameworks = Column(JSONB, default=[])  # Detected frameworks
    hooks = Column(JSONB, default=[])       # Hook patterns
    themes = Column(JSONB, default=[])      # Content themes
    pain_points = Column(JSONB, default=[]) # VOC mining
    desires = Column(JSONB, default=[])     # Customer desires

    # Vector embedding for semantic search (1536 dims for OpenAI)
    embedding = Column(Vector(1536))

    # Metadata
    raw_data = Column(JSONB, default={})
    scraped_at = Column(DateTime, default=func.now())
    analyzed_at = Column(DateTime)

    # Relationships
    author = relationship("AuthorORM", back_populates="contents")
    patterns = relationship("PatternORM", back_populates="content")

    # Indexes
    __table_args__ = (
        Index("idx_contents_platform", "platform"),
        Index("idx_contents_author", "author_id"),
        Index("idx_contents_published", "published_at"),
        Index("idx_contents_engagement", "engagement_rate"),
        # Vector similarity search index (IVFFlat for approximate NN)
        Index(
            "idx_contents_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class FrameworkORM(Base):
    """Copywriting framework analysis results."""
    __tablename__ = "frameworks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(PGUUID(as_uuid=True), ForeignKey("contents.id"), nullable=False)
    framework_type = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0

    # Framework-specific analysis
    components = Column(JSONB, default={})  # E.g., {"attention": "...", "interest": "..."}
    effectiveness_score = Column(Float, default=0.0)
    notes = Column(Text)

    created_at = Column(DateTime, default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_frameworks_content", "content_id"),
        Index("idx_frameworks_type", "framework_type"),
        Index("idx_frameworks_confidence", "confidence"),
    )


class PatternORM(Base):
    """Cross-platform content patterns."""
    __tablename__ = "patterns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pattern_type = Column(String(50), nullable=False)

    # Pattern content
    content_id = Column(PGUUID(as_uuid=True), ForeignKey("contents.id"), nullable=False)
    related_content_ids = Column(JSONB, default=[])  # UUIDs of related content

    # Analysis
    similarity_score = Column(Float, default=0.0)  # Cosine similarity
    description = Column(Text)
    metadata = Column(JSONB, default={})

    detected_at = Column(DateTime, default=func.now())

    # Relationships
    content = relationship("ContentORM", back_populates="patterns")

    # Indexes
    __table_args__ = (
        Index("idx_patterns_type", "pattern_type"),
        Index("idx_patterns_content", "content_id"),
        Index("idx_patterns_similarity", "similarity_score"),
    )


# ===== PYDANTIC SCHEMAS =====

class AuthorBase(BaseModel):
    """Base schema for author data."""
    platform: Platform
    platform_id: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0


class AuthorCreate(AuthorBase):
    """Schema for creating new author."""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuthorRead(AuthorBase):
    """Schema for reading author data."""
    id: UUID
    total_content: int = 0
    avg_engagement: float = 0.0
    authority_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentBase(BaseModel):
    """Base schema for content data."""
    platform: Platform
    source_url: str
    title: Optional[str] = None
    body: str
    content_type: Optional[str] = None
    published_at: Optional[datetime] = None


class ContentCreate(ContentBase):
    """Schema for creating new content."""
    author_id: Optional[UUID] = None

    # Metrics
    likes: int = 0
    views: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0

    # Optional embedding (1536 dimensions)
    embedding: Optional[list[float]] = None

    # Metadata
    raw_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v):
        """Ensure embedding has correct dimensions."""
        if v is not None and len(v) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class ContentRead(ContentBase):
    """Schema for reading content data."""
    id: UUID
    author_id: Optional[UUID] = None

    # Metrics
    likes: int = 0
    views: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0

    # Analysis
    frameworks: list[dict[str, Any]] = Field(default_factory=list)
    hooks: list[dict[str, Any]] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)

    # Timestamps
    scraped_at: datetime
    analyzed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContentUpdate(BaseModel):
    """Schema for updating content analysis."""
    frameworks: Optional[list[dict[str, Any]]] = None
    hooks: Optional[list[dict[str, Any]]] = None
    themes: Optional[list[str]] = None
    pain_points: Optional[list[str]] = None
    desires: Optional[list[str]] = None
    embedding: Optional[list[float]] = None
    analyzed_at: Optional[datetime] = None

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v):
        """Ensure embedding has correct dimensions."""
        if v is not None and len(v) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class FrameworkBase(BaseModel):
    """Base schema for framework analysis."""
    content_id: UUID
    framework_type: FrameworkType
    confidence: float = Field(ge=0.0, le=1.0)


class FrameworkCreate(FrameworkBase):
    """Schema for creating framework analysis."""
    components: dict[str, Any] = Field(default_factory=dict)
    effectiveness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class FrameworkRead(FrameworkBase):
    """Schema for reading framework analysis."""
    id: UUID
    components: dict[str, Any] = Field(default_factory=dict)
    effectiveness_score: float = 0.0
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatternBase(BaseModel):
    """Base schema for content patterns."""
    pattern_type: PatternType
    content_id: UUID


class PatternCreate(PatternBase):
    """Schema for creating content pattern."""
    related_content_ids: list[UUID] = Field(default_factory=list)
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PatternRead(PatternBase):
    """Schema for reading content pattern."""
    id: UUID
    related_content_ids: list[UUID] = Field(default_factory=list)
    similarity_score: float = 0.0
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## FILE 6: backend/db/schema.sql

**Purpose**: Complete PostgreSQL schema with pgvector extension

```sql
-- =============================================================================
-- IAC-032 Unified Scraper Database Schema
-- PostgreSQL 16 + pgvector
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================================================
-- AUTHORS TABLE
-- Stores content creators across all platforms
-- =============================================================================

DROP TABLE IF EXISTS patterns CASCADE;
DROP TABLE IF EXISTS frameworks CASCADE;
DROP TABLE IF EXISTS contents CASCADE;
DROP TABLE IF EXISTS authors CASCADE;

CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    platform_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    bio TEXT,
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    total_content INTEGER DEFAULT 0,
    avg_engagement FLOAT DEFAULT 0.0,
    authority_score FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure unique platform + platform_id combination
    CONSTRAINT unique_platform_author UNIQUE (platform, platform_id)
);

-- Indexes for authors
CREATE INDEX idx_authors_platform ON authors(platform);
CREATE INDEX idx_authors_authority ON authors(authority_score DESC);
CREATE INDEX idx_authors_followers ON authors(follower_count DESC);

-- =============================================================================
-- CONTENTS TABLE
-- Core table for all scraped content with vector embeddings
-- =============================================================================

CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('twitter', 'youtube', 'reddit', 'amazon', 'web')),
    source_url TEXT UNIQUE NOT NULL,

    -- Foreign key to author
    author_id UUID REFERENCES authors(id) ON DELETE SET NULL,

    -- Content data
    title TEXT,
    body TEXT NOT NULL,
    content_type VARCHAR(50),
    published_at TIMESTAMP,

    -- Platform metrics
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,

    -- LLM analysis results (stored as JSONB for flexibility)
    frameworks JSONB DEFAULT '[]',
    hooks JSONB DEFAULT '[]',
    themes JSONB DEFAULT '[]',
    pain_points JSONB DEFAULT '[]',
    desires JSONB DEFAULT '[]',

    -- Vector embedding for semantic search (OpenAI text-embedding-3-small = 1536 dims)
    embedding vector(1536),

    -- Raw scraped data and metadata
    raw_data JSONB DEFAULT '{}',
    scraped_at TIMESTAMP DEFAULT NOW(),
    analyzed_at TIMESTAMP
);

-- Indexes for contents
CREATE INDEX idx_contents_platform ON contents(platform);
CREATE INDEX idx_contents_author ON contents(author_id);
CREATE INDEX idx_contents_published ON contents(published_at DESC);
CREATE INDEX idx_contents_engagement ON contents(engagement_rate DESC);
CREATE INDEX idx_contents_scraped ON contents(scraped_at DESC);

-- Vector similarity search index (IVFFlat for approximate nearest neighbor)
-- Use cosine similarity (most common for text embeddings)
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- =============================================================================
-- FRAMEWORKS TABLE
-- Detected copywriting frameworks in content
-- =============================================================================

CREATE TABLE frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    framework_type VARCHAR(50) NOT NULL CHECK (framework_type IN ('aida', 'pas', 'bab', 'pastor', 'hook', 'other')),
    confidence FLOAT DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Framework-specific breakdown
    components JSONB DEFAULT '{}',
    effectiveness_score FLOAT DEFAULT 0.0 CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for frameworks
CREATE INDEX idx_frameworks_content ON frameworks(content_id);
CREATE INDEX idx_frameworks_type ON frameworks(framework_type);
CREATE INDEX idx_frameworks_confidence ON frameworks(confidence DESC);
CREATE INDEX idx_frameworks_effectiveness ON frameworks(effectiveness_score DESC);

-- =============================================================================
-- PATTERNS TABLE
-- Cross-platform content patterns and relationships
-- =============================================================================

CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN ('cross_platform', 'serial', 'response', 'viral', 'authority')),

    -- Source content
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    related_content_ids JSONB DEFAULT '[]',

    -- Analysis
    similarity_score FLOAT DEFAULT 0.0 CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    description TEXT,
    metadata JSONB DEFAULT '{}',

    detected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for patterns
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_content ON patterns(content_id);
CREATE INDEX idx_patterns_similarity ON patterns(similarity_score DESC);

-- =============================================================================
-- USEFUL QUERIES
-- =============================================================================

-- Find semantically similar content (cosine distance)
-- Usage: Replace $1 with your query embedding (1536-dim vector)
-- SELECT id, source_url, 1 - (embedding <=> $1) as similarity
-- FROM contents
-- WHERE embedding IS NOT NULL
-- ORDER BY embedding <=> $1
-- LIMIT 10;

-- Find cross-platform elaboration (same author, similar content, different platforms)
-- SELECT c1.platform, c2.platform, 1 - (c1.embedding <=> c2.embedding) as similarity
-- FROM contents c1
-- JOIN contents c2 ON c1.author_id = c2.author_id
-- WHERE c1.platform != c2.platform
--   AND c1.embedding IS NOT NULL
--   AND c2.embedding IS NOT NULL
--   AND 1 - (c1.embedding <=> c2.embedding) > 0.85
-- ORDER BY similarity DESC;

-- Get top authorities by platform
-- SELECT platform, display_name, follower_count, authority_score
-- FROM authors
-- WHERE platform = 'twitter'
-- ORDER BY authority_score DESC
-- LIMIT 10;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp for authors
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_authors_updated_at
    BEFORE UPDATE ON authors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update author stats when content is added
CREATE OR REPLACE FUNCTION update_author_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE authors
    SET
        total_content = (SELECT COUNT(*) FROM contents WHERE author_id = NEW.author_id),
        avg_engagement = (SELECT COALESCE(AVG(engagement_rate), 0.0) FROM contents WHERE author_id = NEW.author_id),
        updated_at = NOW()
    WHERE id = NEW.author_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_author_stats_on_content
    AFTER INSERT ON contents
    FOR EACH ROW
    WHEN (NEW.author_id IS NOT NULL)
    EXECUTE FUNCTION update_author_stats();
```

---

## SETUP COMMANDS

Execute these commands in order:

```bash
# 1. Navigate to project root
cd /Users/kjd/01-projects/IAC-032-unified-scraper

# 2. Create backend directory structure
mkdir -p backend/db

# 3. Create Python virtual environment with UV
cd backend
uv venv
source .venv/bin/activate

# 4. Install dependencies
uv pip install -e .

# 5. Create database (if not exists)
createdb unified_scraper_dev 2>/dev/null || echo "Database already exists"

# 6. Apply schema
cd /Users/kjd/01-projects/IAC-032-unified-scraper
psql unified_scraper_dev < backend/db/schema.sql

# 7. Verify installation
python -c "
from backend.db import Database, ContentORM, AuthorORM
db = Database()
health = db.health_check()
print('Database Health Check:')
for k, v in health.items():
    print(f'  {k}: {v}')
"
```

---

## ENVIRONMENT CONFIGURATION

Create `.env` file in project root:

```bash
# /Users/kjd/01-projects/IAC-032-unified-scraper/.env

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=kjd
DB_PASSWORD=
DB_NAME=unified_scraper_dev

# Future additions (for other agents)
# OPENAI_API_KEY=sk-...
# SCRAPER_API_KEY=...
```

---

## VERIFICATION COMMANDS

Run these commands to verify success:

### 1. Check file structure

```bash
# Verify all files created
ls -la /Users/kjd/01-projects/IAC-032-unified-scraper/backend/
ls -la /Users/kjd/01-projects/IAC-032-unified-scraper/backend/db/
```

Expected output:
```
backend/
├── __init__.py
├── pyproject.toml
└── db/
    ├── __init__.py
    ├── connection.py
    ├── models.py
    └── schema.sql
```

### 2. Test database connection

```bash
cd /Users/kjd/01-projects/IAC-032-unified-scraper/backend
source .venv/bin/activate

python -c "
from backend.db.connection import Database
db = Database()
health = db.health_check()
assert health['status'] == 'healthy', f'Database unhealthy: {health}'
print('Database connection: PASS')
print(f'PostgreSQL: {health[\"postgresql_version\"]}')
print(f'pgvector: {health[\"pgvector_version\"]}')
print(f'Pool size: {health[\"pool_size\"]}')
"
```

### 3. Test ORM models

```bash
python -c "
from backend.db import Database, ContentORM, AuthorORM, Platform
from sqlalchemy import inspect

db = Database()
with db.session() as session:
    # Check tables exist
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    required = ['authors', 'contents', 'frameworks', 'patterns']
    for table in required:
        assert table in tables, f'Missing table: {table}'

    print('ORM models: PASS')
    print(f'Tables found: {tables}')
"
```

### 4. Test Pydantic schemas

```bash
python -c "
from backend.db.models import ContentCreate, AuthorCreate, Platform
from datetime import datetime
from uuid import uuid4

# Test author creation
author = AuthorCreate(
    platform=Platform.TWITTER,
    platform_id='dankoe',
    display_name='Dan Koe',
    follower_count=500000
)
print(f'Author schema: {author.model_dump()}')

# Test content creation
content = ContentCreate(
    platform=Platform.TWITTER,
    source_url='https://twitter.com/dankoe/status/123',
    body='Focus is the new intelligence. Here is why...',
    likes=5000,
    engagement_rate=0.05
)
print(f'Content schema: {content.model_dump()}')

print('Pydantic schemas: PASS')
"
```

### 5. Test vector operations

```bash
python -c "
from backend.db import Database, ContentORM, AuthorORM, Platform
from sqlalchemy import text

db = Database()
with db.session() as session:
    # Create test author
    author = AuthorORM(
        platform='twitter',
        platform_id='test_user',
        display_name='Test User'
    )
    session.add(author)
    session.flush()

    # Create test content with embedding
    import random
    test_embedding = [random.random() for _ in range(1536)]

    content = ContentORM(
        platform='twitter',
        source_url=f'https://twitter.com/test/{random.randint(1, 999999)}',
        body='Test content for vector operations',
        author_id=author.id,
        embedding=test_embedding
    )
    session.add(content)
    session.flush()

    # Test vector similarity query
    result = session.execute(
        text('''
            SELECT id, 1 - (embedding <=> :query) as similarity
            FROM contents
            WHERE embedding IS NOT NULL
            LIMIT 1
        '''),
        {'query': str(test_embedding)}
    ).fetchone()

    print(f'Vector query result: {result}')
    print('Vector operations: PASS')

    # Cleanup
    session.rollback()
"
```

### 6. Full integration test

```bash
python -c "
from backend.db import (
    Database,
    ContentORM,
    AuthorORM,
    ContentCreate,
    AuthorCreate,
    Platform
)
import random

db = Database()

# Health check
health = db.health_check()
assert health['status'] == 'healthy'
print(f'1. Health check: PASS')

with db.session() as session:
    # Create author
    author_data = AuthorCreate(
        platform=Platform.TWITTER,
        platform_id=f'agent_alpha_test_{random.randint(1000, 9999)}',
        display_name='Agent Alpha Test',
        follower_count=100
    )
    author = AuthorORM(**author_data.model_dump())
    session.add(author)
    session.flush()
    print(f'2. Author creation: PASS (ID: {author.id})')

    # Create content
    content_data = ContentCreate(
        platform=Platform.TWITTER,
        source_url=f'https://twitter.com/test/status/{random.randint(100000, 999999)}',
        body='Agent Alpha database foundation test content',
        author_id=author.id,
        likes=100,
        engagement_rate=0.05,
        embedding=[random.random() for _ in range(1536)]
    )
    content = ContentORM(
        **content_data.model_dump(exclude={'embedding'}),
        embedding=content_data.embedding
    )
    session.add(content)
    session.flush()
    print(f'3. Content creation: PASS (ID: {content.id})')

    # Verify relationships
    assert content.author.id == author.id
    print(f'4. Relationships: PASS')

    # Cleanup
    session.rollback()

print()
print('=== ALL TESTS PASSED ===')
print('Agent Alpha database foundation is ready!')
print('Other agents can now build on this foundation.')
"
```

---

## SUCCESS CRITERIA CHECKLIST

**Must all pass before completion:**

- [ ] PostgreSQL 16 database created (`unified_scraper_dev`)
- [ ] pgvector extension enabled and working
- [ ] All tables created (authors, contents, frameworks, patterns)
- [ ] Vector column supports 1536 dimensions
- [ ] IVFFlat index created for semantic search
- [ ] SQLAlchemy connection pooling working (20 connections)
- [ ] Pydantic v2 schemas validate correctly
- [ ] ORM models map to database tables
- [ ] Author-Content relationship works
- [ ] Triggers update author stats automatically
- [ ] Health check returns healthy status
- [ ] All verification tests pass

---

## DELIVERABLES SUMMARY

When complete, Agent Alpha should have created:

1. **Backend package structure** - Ready for other agents
2. **Database connection manager** - With QueuePool (20 connections)
3. **SQLAlchemy ORM models** - ContentORM, AuthorORM, PatternORM, FrameworkORM
4. **Pydantic v2 schemas** - Create/Read/Update for all models
5. **PostgreSQL schema** - Full SQL with indexes and triggers
6. **Vector search capability** - 1536-dimension embeddings with cosine similarity
7. **Working tests** - All verification commands pass

---

## WHAT'S NEXT

After Agent Alpha completes:

- **Agent Beta** (API Layer): FastAPI endpoints using your Database class
- **Agent Gamma** (Twitter Scraper): Content ingestion into your schema
- **Agent Delta** (YouTube Scraper): Transcript storage with embeddings
- **Agent Epsilon** (RAG Engine): Semantic queries on your vector indexes

**Your foundation enables the entire pipeline. Build it solid.**

---

## TROUBLESHOOTING

### Common Issues

1. **pgvector not found**
   ```bash
   brew install pgvector
   # Then restart PostgreSQL
   brew services restart postgresql@16
   ```

2. **Database connection refused**
   ```bash
   # Start PostgreSQL
   brew services start postgresql@16
   # Check it's running
   pg_isready
   ```

3. **UV not found**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **Permission denied on database**
   ```bash
   createuser -s $(whoami)
   ```

5. **Vector index creation fails**
   - Ensure sufficient data before creating IVFFlat index
   - May need to adjust `lists` parameter based on data size

---

## IMPORTANT NOTES

1. **DO NOT use pip** - Use UV only (per parent CLAUDE.md)
2. **DO NOT install Python via Homebrew** - Use UV venv
3. **DO NOT skip vector index** - Critical for performance
4. **DO NOT hardcode credentials** - Use .env file
5. **DO commit these files** - Foundation for entire project

---

**Agent Alpha: You are the foundation. Make it bulletproof.**

Generated: 2025-11-16
Project: IAC-032 Unified Scraper
Phase: Day 1 of 3 (Database Foundation)
