# PACKAGE 1: Database Setup (PostgreSQL + pgvector)

**CRITICAL - MUST COMPLETE FIRST**
**This blocks Packages 2-6 - They all need the database**

---

## Mission

Set up PostgreSQL with pgvector extension and create the unified content schema that all scrapers will use.

**Duration**: 1-2 hours
**Risk**: HIGH (if this fails, everything fails)
**Dependencies**: None (runs first)

---

## Context

You are setting up the foundation database for a multi-platform content intelligence system. This database will store scraped content from Twitter, YouTube, Reddit, and blogs in a unified schema with vector embeddings for semantic search.

**Key files to read FIRST**:
1. `CLAUDE.md` - Project overview and architecture
2. `docs/pm/DATABASE_SCHEMA.md` - Complete schema design (600 lines)
3. `docs/pm/DAY2_WORK_PACKAGES.md` - This package detailed specs

---

## Deliverables

Create these files:
```
backend/db/
├── connection.py      # SQLAlchemy connection pooling
├── models.py          # Pydantic + SQLAlchemy models
├── schema.sql         # Table definitions
└── migrations/        # Alembic migrations
    └── 001_initial.sql
```

---

## Step-by-Step Tasks

### 1. Install PostgreSQL 16 + pgvector Extension

**macOS**:
```bash
brew install postgresql@16 pgvector
brew services start postgresql@16

# Verify installation
psql --version  # Should show PostgreSQL 16.x

# Create database
createdb unified_scraper

# Install pgvector extension
psql unified_scraper -c "CREATE EXTENSION vector;"

# Verify vector extension
psql unified_scraper -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
# Expected output: vector | 0.5.x or higher
```

**Linux (Ubuntu/Debian)**:
```bash
# Add PostgreSQL 16 repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL 16
sudo apt install postgresql-16 postgresql-16-pgvector

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb unified_scraper
sudo -u postgres psql unified_scraper -c "CREATE EXTENSION vector;"
```

**Verify setup**:
```bash
psql unified_scraper -c "SELECT version();"
# Expected: PostgreSQL 16.x

psql unified_scraper -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Expected: Row showing vector extension
```

---

### 2. Create Database Schema

**File**: `backend/db/schema.sql`

Copy from `docs/pm/DATABASE_SCHEMA.md` (lines 50-200):

```sql
-- backend/db/schema.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main contents table (unified across all platforms)
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Platform identification
    platform VARCHAR(50) NOT NULL,  -- 'twitter', 'youtube', 'reddit', 'web'
    source_url TEXT NOT NULL UNIQUE,
    external_id VARCHAR(255),  -- Platform's native ID

    -- Author information
    author_id VARCHAR(255) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    author_handle VARCHAR(255),

    -- Content
    content_type VARCHAR(50) NOT NULL,  -- 'tweet', 'video', 'post', 'article'
    title TEXT,
    body TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',

    -- Metrics (JSONB for flexibility)
    metrics JSONB DEFAULT '{}',

    -- AI Analysis (populated by LLM)
    analysis JSONB DEFAULT '{}',

    -- Vector embedding for semantic search
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimensions

    -- Timestamps
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),

    -- Metadata (platform-specific extras)
    metadata JSONB DEFAULT '{}'
);

-- Authors table (deduplicated across platforms)
CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name VARCHAR(255) NOT NULL UNIQUE,  -- Normalized name

    -- Platform accounts
    twitter_handle VARCHAR(255),
    youtube_channel_id VARCHAR(255),
    reddit_username VARCHAR(255),

    -- Aggregated metrics
    total_followers INT DEFAULT 0,
    avg_engagement_rate DECIMAL(5,2) DEFAULT 0.0,

    -- Authority score (calculated)
    authority_score DECIMAL(5,2) DEFAULT 0.0,

    -- Metadata
    bio TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Projects table (user research projects)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Research parameters
    topic TEXT NOT NULL,
    platforms VARCHAR(255)[] DEFAULT ARRAY['twitter', 'youtube', 'reddit'],
    authorities UUID[] DEFAULT ARRAY[]::UUID[],  -- References authors.id

    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'completed', 'archived'

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Patterns table (detected content elaboration patterns)
CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern type
    pattern_type VARCHAR(50) NOT NULL,  -- 'elaboration', 'repurposing', 'thread'

    -- Related contents
    source_content_id UUID REFERENCES contents(id),
    related_content_ids UUID[] NOT NULL,

    -- Similarity metrics
    min_similarity DECIMAL(5,2) NOT NULL,
    avg_similarity DECIMAL(5,2) NOT NULL,

    -- Metadata
    detected_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- INDEXES (CRITICAL FOR PERFORMANCE)
-- ============================================

-- Vector similarity search (IVFFlat for fast approximate search)
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on data size (sqrt(num_rows))

-- Platform filtering
CREATE INDEX idx_contents_platform ON contents(platform);

-- Author filtering
CREATE INDEX idx_contents_author ON contents(author_id);

-- Full-text search on body
CREATE INDEX idx_contents_fts ON contents
USING GIN(to_tsvector('english', body));

-- Date range queries
CREATE INDEX idx_contents_published ON contents(published_at DESC);
CREATE INDEX idx_contents_scraped ON contents(scraped_at DESC);

-- Unique constraint on source URL
CREATE UNIQUE INDEX idx_contents_source_url ON contents(source_url);

-- Author canonical name lookup
CREATE INDEX idx_authors_canonical ON authors(canonical_name);

-- Project status queries
CREATE INDEX idx_projects_status ON projects(status);
```

**Execute schema**:
```bash
psql unified_scraper < backend/db/schema.sql
```

**Verify tables created**:
```bash
psql unified_scraper -c "\dt"
# Expected: contents, authors, projects, patterns
```

---

### 3. Create SQLAlchemy Connection Manager

**File**: `backend/db/connection.py`

```python
"""
Database connection manager with connection pooling.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import os

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost/unified_scraper"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # Max 10 connections
    max_overflow=20,       # Allow 20 additional connections if needed
    pool_pre_ping=True,    # Verify connections before use
    echo=False             # Set True for SQL query logging (debugging)
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Content).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")

            # Test pgvector extension
            result = conn.execute(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
            )
            ext = result.fetchone()
            if ext:
                print(f"✅ pgvector extension: v{ext[1]}")
            else:
                print("❌ pgvector extension not found!")

        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection when run directly
    test_connection()
```

**Test connection**:
```bash
cd backend
python -m db.connection
# Expected: ✅ Connected to PostgreSQL: PostgreSQL 16.x
#           ✅ pgvector extension: v0.5.x
```

---

### 4. Create Pydantic + SQLAlchemy Models

**File**: `backend/db/models.py`

```python
"""
Database models (SQLAlchemy ORM) and Pydantic schemas.
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, ARRAY, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID as PyUUID, uuid4

from .connection import Base


# ============================================
# SQLAlchemy Models (Database Tables)
# ============================================

class Content(Base):
    """Unified content table (tweets, videos, posts, articles)."""
    __tablename__ = "contents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Platform
    platform = Column(String(50), nullable=False, index=True)
    source_url = Column(Text, nullable=False, unique=True)
    external_id = Column(String(255))

    # Author
    author_id = Column(String(255), nullable=False, index=True)
    author_name = Column(String(255), nullable=False)
    author_handle = Column(String(255))

    # Content
    content_type = Column(String(50), nullable=False)
    title = Column(Text)
    body = Column(Text, nullable=False)
    language = Column(String(10), default="en")

    # Metrics and analysis
    metrics = Column(JSONB, default={})
    analysis = Column(JSONB, default={})

    # Vector embedding
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small

    # Timestamps
    published_at = Column(TIMESTAMP)
    scraped_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Metadata
    metadata = Column(JSONB, default={})


class Author(Base):
    """Deduplicated authors across platforms."""
    __tablename__ = "authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    canonical_name = Column(String(255), nullable=False, unique=True)

    # Platform handles
    twitter_handle = Column(String(255))
    youtube_channel_id = Column(String(255))
    reddit_username = Column(String(255))

    # Aggregated metrics
    total_followers = Column(Integer, default=0)
    avg_engagement_rate = Column(Integer, default=0)  # Stored as basis points (0-10000)
    authority_score = Column(Integer, default=0)  # 0-10000

    # Metadata
    bio = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)


class Project(Base):
    """User research projects."""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Research parameters
    topic = Column(Text, nullable=False)
    platforms = Column(ARRAY(String), default=["twitter", "youtube", "reddit"])
    authorities = Column(ARRAY(UUID(as_uuid=True)), default=[])

    # Status
    status = Column(String(50), default="active", index=True)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)


class Pattern(Base):
    """Detected content patterns (elaboration, repurposing)."""
    __tablename__ = "patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    pattern_type = Column(String(50), nullable=False)
    source_content_id = Column(UUID(as_uuid=True))
    related_content_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)

    min_similarity = Column(Integer, nullable=False)  # Basis points (0-10000)
    avg_similarity = Column(Integer, nullable=False)

    detected_at = Column(TIMESTAMP, default=datetime.utcnow)
    metadata = Column(JSONB, default={})


# ============================================
# Pydantic Schemas (API Request/Response)
# ============================================

class UnifiedContent(BaseModel):
    """Unified content schema (platform-agnostic)."""
    content_id: PyUUID = Field(default_factory=uuid4)

    # Platform
    platform: Literal["twitter", "youtube", "reddit", "web"]
    source_url: str
    external_id: Optional[str] = None

    # Author
    author_id: str
    author_name: str
    author_handle: Optional[str] = None

    # Content
    content_type: str  # 'tweet', 'video', 'post', 'article'
    title: Optional[str] = None
    body: str
    language: str = "en"

    # Metrics (flexible JSONB)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Analysis (populated by LLM)
    analysis: Dict[str, Any] = Field(default_factory=dict)

    # Vector embedding
    embedding: Optional[List[float]] = None

    # Timestamps
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PyUUID: lambda v: str(v)
        }


class AuthorModel(BaseModel):
    """Author metadata."""
    id: PyUUID = Field(default_factory=uuid4)
    canonical_name: str

    twitter_handle: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    reddit_username: Optional[str] = None

    total_followers: int = 0
    avg_engagement_rate: float = 0.0  # Percentage
    authority_score: float = 0.0  # 0-100

    bio: Optional[str] = None
```

**Test models**:
```python
# backend/test_models.py
from db.models import UnifiedContent
from datetime import datetime

# Create test content
content = UnifiedContent(
    platform="twitter",
    source_url="https://twitter.com/dankoe/status/123",
    author_id="dankoe",
    author_name="Dan Koe",
    author_handle="@dankoe",
    content_type="tweet",
    body="Focus is the new currency.",
    metrics={"likes": 1234, "retweets": 567}
)

print(content.json(indent=2))
# Expected: Valid JSON with all fields
```

---

### 5. Test Vector Similarity Search

**File**: `backend/db/test_vectors.py`

```python
"""
Test vector similarity search functionality.
"""
from sqlalchemy import text
from db.connection import engine
import random

def test_vector_search():
    """Test pgvector similarity search."""

    # Generate random test embedding (1536 dimensions)
    test_embedding = [random.random() for _ in range(1536)]

    # Insert test data
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO contents (
                platform, source_url, author_id, author_name,
                content_type, body, embedding
            ) VALUES (
                'twitter', 'https://test.com/1', 'test_user', 'Test User',
                'tweet', 'This is a test tweet about focus systems.',
                :embedding
            )
        """), {"embedding": str(test_embedding)})

        conn.commit()

        # Test similarity search
        result = conn.execute(text("""
            SELECT
                body,
                1 - (embedding <=> :query_embedding) as similarity
            FROM contents
            ORDER BY embedding <=> :query_embedding
            LIMIT 5
        """), {"query_embedding": str(test_embedding)})

        print("\n✅ Vector Similarity Search Test:")
        for row in result:
            print(f"  Similarity: {row[1]:.4f} | Body: {row[0][:50]}...")

        # Clean up test data
        conn.execute(text("DELETE FROM contents WHERE source_url = 'https://test.com/1'"))
        conn.commit()

    print("\n✅ Vector search working correctly!")

if __name__ == "__main__":
    test_vector_search()
```

**Run test**:
```bash
cd backend
python -m db.test_vectors
# Expected: ✅ Vector Similarity Search Test
#           ✅ Vector search working correctly!
```

---

## Success Criteria (Must Pass All)

- [ ] `psql unified_scraper -c "SELECT version();"` returns PostgreSQL 16.x
- [ ] `psql unified_scraper -c "SELECT * FROM pg_extension WHERE extname = 'vector';"` shows vector extension
- [ ] `psql unified_scraper -c "\dt"` shows 4 tables (contents, authors, projects, patterns)
- [ ] `psql unified_scraper -c "\di"` shows 8+ indexes including `idx_contents_embedding`
- [ ] `python -m db.connection` connects successfully
- [ ] `python -m db.test_vectors` runs without errors
- [ ] Vector similarity query returns in <500ms (test with 100 rows)

---

## Troubleshooting

### Issue: pgvector extension not found
```bash
# macOS
brew reinstall pgvector

# Linux
sudo apt install postgresql-16-pgvector

# Then recreate extension
psql unified_scraper -c "CREATE EXTENSION vector;"
```

### Issue: Permission denied creating database
```bash
# macOS
createdb unified_scraper

# Linux
sudo -u postgres createdb unified_scraper
sudo -u postgres psql unified_scraper
```

### Issue: Connection refused
```bash
# Check PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql     # Linux

# Start if needed
brew services start postgresql@16         # macOS
sudo systemctl start postgresql           # Linux
```

---

## Commit Message Template

```
feat(db): Setup PostgreSQL with pgvector and unified schema

- Install PostgreSQL 16 + pgvector extension
- Create unified_scraper database
- Implement unified content schema (4 tables)
- Add vector similarity indexes (IVFFlat, cosine)
- SQLAlchemy connection pooling (10 connections)
- Pydantic models for API validation
- Test vector similarity search (<500ms)

Tables:
- contents: Main table with vector(1536) embedding
- authors: Deduplicated across platforms
- projects: User research projects
- patterns: Cross-platform elaboration detection

Indexes:
- Vector: IVFFlat cosine similarity
- Platform, author, published_at (filtering)
- Full-text search (GIN on body)

Tests: ✅ Connection, ✅ Vector search

Ref: docs/pm/DATABASE_SCHEMA.md, Package 1
Blocks: Packages 2-6 (all need database)
```

---

## After Completion

**Notify in GitHub**:
1. Close issue #X (Database Setup)
2. Comment: "✅ Database ready. Packages 2-6 can start."

**Update SESSION_STATUS.md**:
- Package 1: ✅ COMPLETE
- Database URL: `postgresql://localhost/unified_scraper`
- Ready for parallel execution: Packages 2-6

**Next**: Spawn Packages 2-6 in parallel (5 CCW agents simultaneously)

---

**Questions before starting?** Read `docs/pm/DATABASE_SCHEMA.md` for full schema details.

**Stuck?** Check troubleshooting section above or ask in issue comments.

**Let's build this foundation!** 🚀
