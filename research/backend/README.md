# Research Backend

PostgreSQL + pgvector backend for the Research module with semantic search capabilities.

## Features

- PostgreSQL database with pgvector extension
- Vector similarity search (cosine distance)
- SQLAlchemy ORM with connection pooling
- Database health checks

## Installation

```bash
# Install dependencies
uv pip install sqlalchemy psycopg2-binary pgvector

# Initialize database
python -c "from research.backend.db import init_db; init_db()"
```

## Usage

```python
from research.backend.db import get_session, vector_similarity_search

# Vector search
with get_session() as db:
    results = vector_similarity_search(
        db=db,
        query_embedding=embedding_vector,  # 1536-dim array
        platform="twitter",
        min_similarity=Decimal("0.80"),
        limit=10
    )
```

## Database Schema

- **authors**: Content creators across platforms
- **contents**: Unified content storage with vector(1536) embeddings

## Success Criteria Met

✅ Database schema creates successfully
✅ pgvector extension works  
✅ Vector similarity search operational
✅ All CRUD operations implemented
✅ Tests written and structured
