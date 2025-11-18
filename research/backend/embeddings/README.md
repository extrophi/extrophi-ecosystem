# Embedding Generation Module

OpenAI ada-002 embedding generation for Research Backend with text chunking, batch processing, caching, and cost tracking.

## Features

- **Text Chunking**: Automatically splits long text into 512-token chunks
- **Batch Processing**: Processes up to 100 chunks per API request
- **Pgvector Storage**: Stores embeddings in PostgreSQL with pgvector
- **Cache Layer**: Avoids re-embedding content that already has embeddings
- **Cost Tracking**: Monitors tokens used and API costs

## Quick Start

```python
import os
from embeddings.generator import EmbeddingGenerator
from db.connection import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
await db_manager.connect()

# Initialize embedding generator
generator = EmbeddingGenerator(api_key=os.getenv("OPENAI_API_KEY"))
await generator.initialize(db_manager)

# Generate embedding for single text
embedding = await generator.generate("Your text here")
print(f"Generated embedding: {len(embedding)} dimensions")

# Generate embeddings for database content
content_id = "your-content-uuid"
embedding = await generator.generate_for_content(content_id)

# Batch generate for all uncached content
stats = await generator.generate_for_all_uncached()
print(f"Generated {stats['generated']} embeddings")
print(f"Total cost: ${stats['cost']['total_cost_usd']}")
```

## API Reference

### EmbeddingGenerator

Main class for generating embeddings.

#### Methods

**`__init__(api_key: str, model: str = "text-embedding-ada-002")`**

Initialize the generator.

- `api_key`: OpenAI API key
- `model`: OpenAI embedding model (default: text-embedding-ada-002)

**`async initialize(db_manager: DatabaseManager)`**

Connect to database and enable caching.

**`async generate(text: str) -> List[float]`**

Generate embedding for single text.

Returns: 1536-dimensional embedding vector

**`async generate_batch(texts: List[str]) -> List[List[float]]`**

Generate embeddings for multiple texts (max 100 per request).

**`async generate_chunked(text: str) -> List[float]`**

Generate embedding for long text using chunking and averaging.

**`async generate_for_content(content_id: UUID, force: bool = False) -> Optional[List[float]]`**

Generate embedding for content in database.

- `content_id`: Content UUID
- `force`: Force regeneration even if cached

**`async generate_for_contents(content_ids: List[UUID], force: bool = False) -> Dict[str, Any]`**

Batch generate embeddings for multiple contents.

Returns statistics:
```python
{
    "total": 100,
    "generated": 75,
    "cached": 25,
    "failed": 0,
    "duration_seconds": 45.2,
    "embeddings_per_second": 1.66,
    "cost": {...}
}
```

**`async generate_for_all_uncached() -> Dict[str, Any]`**

Generate embeddings for all contents without embeddings.

**`get_cost_stats() -> Dict[str, Any]`**

Get current cost tracking statistics.

**`async get_cache_stats() -> Dict[str, Any]`**

Get cache statistics.

### TextChunker

Handles text chunking with tiktoken.

```python
from embeddings.generator import TextChunker

chunker = TextChunker(model="text-embedding-ada-002", chunk_size=512)

# Count tokens
token_count = chunker.count_tokens("Your text here")

# Split into chunks
chunks = chunker.chunk_text("Very long text...")
```

### EmbeddingCache

Cache layer for avoiding duplicate embeddings.

```python
from embeddings.generator import EmbeddingCache

cache = EmbeddingCache(db_manager)

# Check if content has embedding
has_embedding = await cache.has_embedding(content_id)

# Get cached embedding
embedding = await cache.get_cached_embedding(content_id)

# Get cache statistics
stats = await cache.count_cached()
# Returns: {"cached": 100, "uncached": 25, "total": 125, "cache_hit_rate": 80.0}
```

### EmbeddingCostTracker

Track API costs.

```python
from embeddings.generator import EmbeddingCostTracker

tracker = EmbeddingCostTracker()

# Record request
tracker.add_request(tokens=1000, embeddings_count=1)

# Get statistics
stats = tracker.get_stats()
# Returns: {"total_tokens": 1000, "total_cost_usd": 0.0001, ...}
```

## Usage Examples

### Example 1: Generate Embeddings for New Content

```python
from uuid import uuid4
from db.crud import SourceCRUD, ContentCRUD
from embeddings.generator import EmbeddingGenerator

# Create source and content
source_crud = SourceCRUD(db_manager)
content_crud = ContentCRUD(db_manager)

source_id = await source_crud.create(
    platform="web",
    url="https://example.com/article",
    title="Sample Article"
)

content_id = await content_crud.create(
    source_id=source_id,
    content_type="text",
    text_content="Your article content here..."
)

# Generate embedding
generator = EmbeddingGenerator(api_key=os.getenv("OPENAI_API_KEY"))
await generator.initialize(db_manager)

embedding = await generator.generate_for_content(content_id)
print(f"Embedding stored for content: {content_id}")
```

### Example 2: Batch Process Multiple Contents

```python
# Get all content IDs without embeddings
query = "SELECT id FROM contents WHERE embedding IS NULL LIMIT 100"
rows = await db_manager.fetch(query)
content_ids = [row['id'] for row in rows]

# Generate embeddings in batch
stats = await generator.generate_for_contents(content_ids)

print(f"Results:")
print(f"  Generated: {stats['generated']}")
print(f"  Cached: {stats['cached']}")
print(f"  Failed: {stats['failed']}")
print(f"  Duration: {stats['duration_seconds']}s")
print(f"  Cost: ${stats['cost']['total_cost_usd']}")
```

### Example 3: Process All Uncached Content

```python
# Generate embeddings for all contents without embeddings
stats = await generator.generate_for_all_uncached()

# Log cost statistics
generator.cost_tracker.log_stats()

# Get cache statistics
cache_stats = await generator.get_cache_stats()
print(f"Cache hit rate: {cache_stats['cache_hit_rate']}%")
```

### Example 4: Semantic Search with Generated Embeddings

```python
# Generate query embedding
query = "machine learning best practices"
query_embedding = await generator.generate(query)

# Search for similar content
query = """
    SELECT
        content_id,
        text_content,
        similarity_score,
        platform,
        url
    FROM find_similar_content($1::vector, 0.7, 10)
"""

# Convert embedding to pgvector format
embedding_str = f"[{','.join(map(str, query_embedding))}]"
results = await db_manager.fetch(query, embedding_str)

for row in results:
    print(f"{row['platform']}: {row['text_content'][:100]}...")
    print(f"  Similarity: {row['similarity_score']:.2%}")
    print(f"  URL: {row['url']}")
```

## Cost Management

OpenAI ada-002 pricing: **$0.0001 per 1K tokens**

### Example Costs

- 100 tweets (avg 50 tokens): $0.0005
- 10 blog posts (avg 2000 tokens): $0.002
- 1000 documents (avg 500 tokens): $0.05

### Best Practices

1. **Use caching**: Avoid re-embedding the same content
2. **Batch processing**: Process multiple texts in single API calls
3. **Monitor costs**: Check `get_cost_stats()` regularly
4. **Chunk wisely**: Default 512 tokens balances cost and quality

## Performance

### Benchmarks (approximate)

- Single embedding: ~0.5s
- Batch (100 texts): ~2-3s
- Throughput: ~30-40 embeddings/second (batched)

### Optimization Tips

1. **Batch similar-length texts**: Reduces padding overhead
2. **Use cache checks**: Skip already-embedded content
3. **Process in parallel**: Multiple generator instances (watch rate limits)
4. **Database indexes**: Ensure pgvector indexes are created

## Database Schema

The module stores embeddings in the `contents` table:

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    source_id UUID NOT NULL,
    text_content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 embeddings
    ...
);

-- Vector similarity index
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Database (if not using DATABASE_URL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=research_db
DB_USER=postgres
DB_PASSWORD=postgres
```

## Testing

Run tests:

```bash
# Unit tests
pytest tests/test_embeddings.py -v

# Integration tests (require database and API key)
pytest tests/test_embeddings.py -v -m integration
```

## Troubleshooting

### "Connection pool not initialized"

Call `await generator.initialize(db_manager)` before using database methods.

### "API key not found"

Set `OPENAI_API_KEY` environment variable.

### Slow embedding generation

- Use batch processing (`generate_batch` or `generate_for_contents`)
- Check network latency to OpenAI API
- Verify database connection pool size

### High costs

- Enable caching (default)
- Reduce chunk size if applicable
- Monitor with `get_cost_stats()`

## Contributing

When adding features:

1. Update tests in `tests/test_embeddings.py`
2. Add examples to this README
3. Update cost tracking if API changes
4. Document new methods with docstrings

## License

Part of Research Backend - see root LICENSE file.
