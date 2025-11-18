# Database Module - PostgreSQL + pgvector

This module provides PostgreSQL database functionality with pgvector extension for semantic content search.

## Overview

The database module includes:

- **PostgreSQL schema** with pgvector extension
- **Vector embeddings table** for semantic search
- **CRUD operations** for sources, contents, and scrape jobs
- **Vector similarity search** using cosine similarity
- **Connection pooling** with asyncpg
- **Comprehensive tests** with pytest

## Quick Start

### 1. Install PostgreSQL and pgvector

**macOS:**
```bash
brew install postgresql@16 pgvector
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Install pgvector:**
```bash
# Clone and build pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 2. Configure Environment Variables

Create `.env` file in `research/backend/`:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/research_db

# Or use individual components:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=research_db
DB_USER=postgres
DB_PASSWORD=postgres
```

### 3. Install Python Dependencies

```bash
cd research/backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 4. Initialize Database

Run the initialization script:

```bash
python -m db.init_db
```

This will:
- Create the `research_db` database (if not exists)
- Enable pgvector extension
- Create tables (sources, contents, scrape_jobs)
- Create indexes for performance
- Create vector similarity search functions
- Insert sample data
- Verify setup

### 5. Verify Setup

Start the API server:

```bash
uvicorn main:app --reload
```

Check health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "pgvector": "enabled"
  }
}
```

## Database Schema

### Tables

#### `sources`
Stores content sources from various platforms.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,      -- twitter, youtube, reddit, web
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `contents`
Stores scraped content with vector embeddings.

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES sources(id),
    content_type VARCHAR(50) NOT NULL,  -- text, transcript, post, comment
    text_content TEXT NOT NULL,
    embedding vector(1536),             -- OpenAI ada-002 embeddings
    word_count INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `scrape_jobs`
Tracks asynchronous scraping jobs.

```sql
CREATE TABLE scrape_jobs (
    id UUID PRIMARY KEY,
    url TEXT NOT NULL,
    platform VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    depth INTEGER DEFAULT 1,
    extract_embeddings BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_seconds REAL,
    items_scraped INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

- **Vector similarity index** (IVFFlat) on `contents.embedding` for fast approximate search
- **Platform indexes** for filtering by source
- **Timestamp indexes** for sorting by date
- **GIN indexes** on JSONB metadata fields

### Functions

#### `find_similar_content(query_embedding, threshold, count)`
Finds content similar to query embedding across all platforms.

```sql
SELECT * FROM find_similar_content(
    '[0.1, 0.2, ...]'::vector,  -- Query embedding (1536 dims)
    0.7,                         -- Similarity threshold (0.0-1.0)
    10                           -- Max results
);
```

#### `find_similar_content_by_platform(query_embedding, platform, threshold, count)`
Finds similar content filtered by platform.

```sql
SELECT * FROM find_similar_content_by_platform(
    '[0.1, 0.2, ...]'::vector,
    'twitter',
    0.7,
    10
);
```

#### `get_content_statistics()`
Returns statistics by platform.

```sql
SELECT * FROM get_content_statistics();
```

## Python API

### Connection Management

```python
from db import get_db_manager

# Get database manager (singleton)
db_manager = get_db_manager()

# Connect (usually done in app startup)
await db_manager.connect(min_size=10, max_size=20)

# Health check
health = await db_manager.health_check()

# Disconnect (usually done in app shutdown)
await db_manager.disconnect()
```

### CRUD Operations

#### Source CRUD

```python
from db import SourceCRUD, get_db_manager

db = get_db_manager()
source_crud = SourceCRUD(db)

# Create source
source_id = await source_crud.create(
    platform="twitter",
    url="https://twitter.com/user/status/123",
    title="Tweet Title",
    author="@username",
    metadata={"tweet_id": "123"}
)

# Get source
source = await source_crud.get_by_id(source_id)
source = await source_crud.get_by_url(url)

# List sources
sources = await source_crud.list_by_platform("twitter", limit=50)

# Update source
await source_crud.update(source_id, title="Updated Title")

# Delete source (cascades to contents)
await source_crud.delete(source_id)
```

#### Content CRUD

```python
from db import ContentCRUD, get_db_manager

db = get_db_manager()
content_crud = ContentCRUD(db)

# Create content
content_id = await content_crud.create(
    source_id=source_id,
    content_type="text",
    text_content="This is the content...",
    embedding=[0.1, 0.2, ...],  # 1536 dimensions
    metadata={"language": "en"}
)

# Get content
content = await content_crud.get_by_id(content_id)

# List by source
contents = await content_crud.list_by_source(source_id, limit=50)

# Update embedding
await content_crud.update_embedding(content_id, embedding)

# Count
with_embeddings = await content_crud.count_with_embeddings()
without_embeddings = await content_crud.count_without_embeddings()
```

#### Scrape Job CRUD

```python
from db import ScrapeJobCRUD, get_db_manager

db = get_db_manager()
job_crud = ScrapeJobCRUD(db)

# Create job
job_id = await job_crud.create(
    url="https://example.com",
    platform="web",
    depth=2,
    extract_embeddings=True
)

# Update status
await job_crud.update_status(job_id, "processing")
await job_crud.update_status(
    job_id,
    "completed",
    items_scraped=10
)

# Handle errors
await job_crud.update_status(
    job_id,
    "failed",
    error_message="Connection timeout"
)

# List jobs
pending = await job_crud.list_pending(limit=10)
jobs = await job_crud.list_by_status("completed", limit=50)

# Statistics
stats = await job_crud.get_statistics()
```

### Vector Similarity Search

```python
from db import VectorSearch, get_db_manager

db = get_db_manager()
search = VectorSearch(db)

# Find similar content (all platforms)
results = await search.find_similar(
    query_embedding=[0.1, 0.2, ...],  # 1536 dimensions
    match_threshold=0.7,               # Min similarity (0.0-1.0)
    match_count=10                     # Max results
)

# Find similar by platform
results = await search.find_similar_by_platform(
    query_embedding=[0.1, 0.2, ...],
    platform="twitter",
    match_threshold=0.7,
    match_count=10
)

# Find similar to existing content
results = await search.find_similar_by_content_id(
    content_id=content_id,
    match_threshold=0.7,
    match_count=10,
    exclude_self=True
)

# Hybrid search (text + vector)
results = await search.search_by_text_and_vector(
    text_query="machine learning AI",
    query_embedding=[0.1, 0.2, ...],
    match_threshold=0.7,
    match_count=10
)

# Batch search
query_embeddings = [[0.1, ...], [0.2, ...], [0.3, ...]]
results = await search.batch_find_similar(
    query_embeddings=query_embeddings,
    match_threshold=0.7,
    match_count=10
)

# Get statistics
stats = await search.get_content_statistics()
```

## Testing

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_connection.py

# With coverage
pytest --cov=db --cov-report=term-missing

# Verbose output
pytest -v
```

### Test Database

Tests use a separate test database (`research_db_test` by default).

Set test database in environment:
```bash
export TEST_DB_NAME=research_db_test
```

Or create `.env.test`:
```bash
TEST_DB_NAME=research_db_test
```

### Test Coverage

Current test coverage includes:
- Connection pooling
- CRUD operations for all tables
- Vector similarity search
- Database health checks
- Error handling
- Transaction management

## Performance Optimization

### Vector Index

The IVFFlat index provides fast approximate nearest neighbor search:

```sql
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Index parameters:**
- `lists = 100` for < 100K rows
- `lists = 1000` for 100K - 1M rows
- `lists = rows / 1000` as a general rule

### Connection Pooling

Adjust pool size based on load:

```python
await db_manager.connect(
    min_size=10,  # Minimum connections
    max_size=20   # Maximum connections
)
```

**Guidelines:**
- Development: min=2, max=5
- Production: min=10, max=20
- High traffic: min=20, max=50

### Query Optimization

- Use indexes for frequently filtered columns
- Limit result sets with `LIMIT`
- Use batch operations for bulk inserts
- Monitor slow queries with `pg_stat_statements`

## Troubleshooting

### pgvector extension not found

```bash
# Check if pgvector is installed
psql -d research_db -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Install pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Connection refused

```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql@16  # macOS
sudo systemctl start postgresql     # Linux
```

### Permission denied

```bash
# Grant permissions
psql -d research_db -c "GRANT ALL ON SCHEMA public TO postgres;"
psql -d research_db -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;"
```

### Slow vector search

```bash
# Rebuild index with more lists
DROP INDEX idx_contents_embedding;
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000);  -- Increase for larger datasets
```

## Migration Guide

To update schema in production:

1. **Backup database:**
   ```bash
   pg_dump research_db > backup_$(date +%Y%m%d).sql
   ```

2. **Test migration on backup:**
   ```bash
   createdb research_db_test
   psql research_db_test < backup_20250101.sql
   psql research_db_test < migration.sql
   ```

3. **Apply to production:**
   ```bash
   psql research_db < migration.sql
   ```

4. **Verify:**
   ```bash
   python -m db.init_db  # Verification only
   ```

## Next Steps

- **LAMBDA Agent**: Implement embedding generation (OpenAI ada-002)
- **IOTA Agent**: Implement platform scrapers (Twitter, YouTube, Reddit, Web)
- **MU Agent**: Integrate all components for enrichment pipeline

## References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
