# Local Vector Database Service

## Overview

This service provides **FREE, local semantic search** using LanceDB and Sentence Transformers, eliminating the need for expensive OpenAI API calls for embeddings.

## Architecture

### Components

1. **LanceDB**: Local, serverless vector database
   - No server setup required
   - Embedded directly in the application
   - Persistent storage on disk
   - Fast vector similarity search

2. **Sentence Transformers**: Free, local embedding model
   - Model: `all-MiniLM-L6-v2`
   - Dimensions: 384 (vs OpenAI's 1536)
   - Size: 80MB download
   - Speed: 50-100 texts/second on CPU
   - Runs locally (CPU or GPU)

3. **Integration**: Works with existing PostgreSQL content database
   - Syncs content from PostgreSQL
   - Generates embeddings locally
   - Provides semantic search API

## Features

- ✅ **100% Free**: No API costs (vs $0.10 per 1M tokens for OpenAI)
- ✅ **Privacy**: All processing happens locally
- ✅ **Fast**: <10ms search latency for 10K vectors
- ✅ **Compact**: 384-dim embeddings (1.5KB per vector)
- ✅ **Metadata Filtering**: Search by platform, author, subject
- ✅ **Batch Processing**: Efficient batch embedding generation

## Installation

### Dependencies

```bash
pip install lancedb sentence-transformers torch
```

Or from requirements.txt:

```bash
pip install -r backend/requirements.txt
```

### First-time Setup

The service automatically downloads the embedding model (~80MB) on first use:

```python
from backend.services.vector_db_service import get_vector_db_service

# Initialize service (downloads model if needed)
vector_db = get_vector_db_service()
```

## Usage

### 1. Populate Vector Database

Sync content from PostgreSQL to local vector database:

```bash
# From project root
python -m backend.services.populate_vector_db
```

This will:
- Connect to PostgreSQL database
- Fetch all content entries
- Generate embeddings using local model
- Store vectors in LanceDB

### 2. Test Semantic Search

Run test queries:

```bash
python -m backend.services.test_vector_search
```

Test queries include:
- "How to build an audience"
- "Marketing frameworks"
- "First principles thinking"
- And more...

### 3. Use in Your Code

```python
from backend.services.vector_db_service import get_vector_db_service

# Get service instance
vector_db = get_vector_db_service()

# Add content
vector_db.add_content(
    content_id="123",
    text="How to build an audience from scratch...",
    metadata={
        "platform": "twitter",
        "author": "Dan Koe",
        "subject": "marketing"
    }
)

# Semantic search
results = vector_db.search(
    query="audience building strategies",
    limit=10
)

for result in results:
    print(f"Score: {result['similarity_score']:.4f}")
    print(f"Text: {result['text'][:100]}...")
    print(f"Source: {result['metadata']['platform']}")
    print()
```

### 4. Batch Operations

```python
# Batch add content
content_items = [
    {
        "id": "1",
        "text": "First piece of content...",
        "metadata": {"platform": "twitter"}
    },
    {
        "id": "2",
        "text": "Second piece of content...",
        "metadata": {"platform": "youtube"}
    }
]

vector_db.add_content_batch(content_items, generate_embeddings=True)
```

### 5. Metadata Filtering

```python
# Search only Twitter content
results = vector_db.search(
    query="marketing frameworks",
    limit=10,
    filter_metadata={"platform": "twitter"}
)

# Search by author
results = vector_db.search(
    query="content creation",
    filter_metadata={"author": "Dan Koe"}
)
```

## API Reference

### LocalVectorDBService

#### Methods

**`add_content(content_id, text, metadata, embedding)`**
- Add single content item to vector database
- Auto-generates embedding if not provided

**`add_content_batch(content_items, generate_embeddings)`**
- Batch add multiple content items
- More efficient for large datasets

**`search(query, limit, filter_metadata)`**
- Semantic search by text query
- Returns top N similar items
- Optional metadata filtering

**`search_by_embedding(query_embedding, limit)`**
- Search using pre-computed embedding vector

**`get_by_id(content_id)`**
- Retrieve content by ID

**`delete(content_id)`**
- Delete content by ID

**`count()`**
- Get total number of vectors

**`get_statistics()`**
- Get database statistics (size, count, etc.)

**`health_check()`**
- Check service health and performance

## Performance

### Benchmarks

- **Embedding Generation**: ~50-100 texts/second (CPU)
- **Search Latency**: <10ms for 10K vectors
- **Storage**: ~1.5KB per vector (384 dims)
- **Model Load Time**: ~2 seconds (first use)

### Comparison: OpenAI vs Local

| Metric | OpenAI ada-002 | Sentence Transformers |
|--------|----------------|----------------------|
| Dimensions | 1536 | 384 |
| Cost per 1M tokens | $0.10 | $0 (free) |
| Latency | 50-200ms (API) | 10-20ms (local) |
| Storage per vector | 6KB | 1.5KB |
| Privacy | Cloud | Local |
| Rate limits | Yes | No |

## Database Schema

### LanceDB Table: `content_vectors`

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique content identifier |
| text | string | Full text content |
| vector | float[384] | Embedding vector |
| metadata | json | Platform, author, subject, etc. |
| created_at | datetime | Timestamp |

### Metadata Fields

- `platform`: twitter, youtube, reddit, web
- `author`: Content creator/author
- `source`: Source title or URL
- `content_type`: text, transcript, post, comment
- `subject`: ultra_learning, marketing, etc.
- `url`: Original content URL

## Integration with Research Backend

### Architecture

```
PostgreSQL (sources + contents)
        ↓
populate_vector_db.py
        ↓
LanceDB (local vectors)
        ↓
Semantic Search API
        ↓
Enrichment Engine
```

### Workflow

1. **Content Scraping**: Scrapers fetch content → PostgreSQL
2. **Embedding Generation**: populate_vector_db.py → LanceDB
3. **Semantic Search**: API queries LanceDB → Returns similar content
4. **Enrichment**: Results fed to LLM for suggestions

## Configuration

### Environment Variables

```bash
# Optional: Custom vector database path
VECTOR_DB_PATH=./data/lancedb

# Device for embeddings (cpu, cuda, or auto)
EMBEDDING_DEVICE=cpu
```

### Default Configuration

- **Database Path**: `./data/lancedb`
- **Table Name**: `content_vectors`
- **Model**: `all-MiniLM-L6-v2`
- **Device**: Auto-detect (CPU or CUDA)

## Troubleshooting

### Model Download Issues

If model download fails:

```python
from sentence_transformers import SentenceTransformer

# Force download
model = SentenceTransformer('all-MiniLM-L6-v2')
```

### Memory Issues

For large datasets:

```python
# Use smaller batch size
vector_db.add_content_batch(items, batch_size=32)
```

### Slow Performance

Enable GPU acceleration:

```python
# Use CUDA if available
vector_db = LocalVectorDBService(device='cuda')
```

## Roadmap

### Phase 1 (Current)
- ✅ Local vector database setup
- ✅ Sentence transformer embeddings
- ✅ Semantic search API
- ✅ Metadata filtering

### Phase 2 (Next)
- [ ] Incremental updates (sync only new content)
- [ ] Multi-model support (different embedding models)
- [ ] Hybrid search (vector + keyword)
- [ ] Automatic reindexing

### Phase 3 (Future)
- [ ] Distributed vector database
- [ ] Real-time embedding generation
- [ ] Advanced filtering (date ranges, etc.)
- [ ] Vector compression

## Contributing

When adding new features:

1. Update `vector_db_service.py` with new methods
2. Add tests to `test_vector_search.py`
3. Update this README
4. Update API documentation

## License

Part of the Extrophi Ecosystem - IAC-033

## Credits

- **LanceDB**: https://lancedb.com
- **Sentence Transformers**: https://www.sbert.net
- **Model**: all-MiniLM-L6-v2 by Microsoft
