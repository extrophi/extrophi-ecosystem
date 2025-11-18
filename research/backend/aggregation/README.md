# Multi-Source Aggregation Module (CHI-2)

**Agent**: CHI-2
**Duration**: 1.5 hours
**Status**: ✅ Complete

## Overview

The Multi-Source Aggregation module provides a unified timeline view combining content from multiple platforms (Twitter, YouTube, Reddit, Web) with intelligent deduplication and flexible filtering.

## Features

### 1. Unified Timeline
Combines content from multiple platforms into a single chronological view.

**Endpoint**: `GET /api/timeline`

**Query Parameters**:
- `platforms` (optional): Comma-separated list of platforms (e.g., "twitter,youtube,reddit")
- `limit` (default: 50): Maximum results (1-200)
- `offset` (default: 0): Pagination offset
- `sort_by` (default: "published_at"): Sort field (published_at, scraped_at)
- `sort_order` (default: "desc"): Sort order (asc, desc)
- `deduplicate` (default: true): Enable intelligent deduplication
- `similarity_threshold` (default: 0.85): Deduplication threshold (0.0-1.0)

**Example Request**:
```bash
curl "http://localhost:8000/api/timeline?platforms=twitter,youtube&limit=20&deduplicate=true"
```

**Example Response**:
```json
{
  "items": [
    {
      "content_id": "uuid",
      "platform": "twitter",
      "content_type": "post",
      "title": "Thread title",
      "text_content": "Content text...",
      "word_count": 150,
      "language": "en",
      "author": "username",
      "url": "https://twitter.com/...",
      "published_at": "2025-11-18T12:00:00",
      "scraped_at": "2025-11-18T13:00:00",
      "metadata": {}
    }
  ],
  "total": 500,
  "count": 20,
  "platforms": ["twitter", "youtube"],
  "deduplicated_count": 3,
  "pagination": {
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### 2. Source Filtering
Show or hide specific platforms in the timeline.

```bash
# Only Twitter and YouTube
curl "http://localhost:8000/api/timeline?platforms=twitter,youtube"

# All platforms (default)
curl "http://localhost:8000/api/timeline"
```

### 3. Deduplication
Automatically detects and removes duplicate content across platforms using vector embeddings.

**How it works**:
1. Compares embeddings using cosine similarity
2. Detects content with similarity above threshold (default: 0.85)
3. Keeps the earliest published version
4. Returns deduplicated count in response

```bash
# Enable deduplication with custom threshold
curl "http://localhost:8000/api/timeline?deduplicate=true&similarity_threshold=0.90"

# Disable deduplication
curl "http://localhost:8000/api/timeline?deduplicate=false"
```

### 4. Platform Statistics
Get overview of available content by platform.

**Endpoint**: `GET /api/timeline/statistics`

**Example Response**:
```json
{
  "platforms": [
    {
      "platform": "twitter",
      "content_count": 250,
      "source_count": 50,
      "author_count": 25,
      "avg_word_count": 180.5,
      "earliest_published": "2025-01-01T00:00:00",
      "latest_published": "2025-11-18T12:00:00",
      "latest_scraped": "2025-11-18T13:00:00"
    }
  ],
  "total_content": 500,
  "total_sources": 100,
  "total_authors": 50
}
```

### 5. Author Filtering
View content from a specific author across all platforms.

**Endpoint**: `GET /api/timeline/author/{author}`

**Query Parameters**:
- `platforms` (optional): Filter by platforms
- `limit` (default: 50): Maximum results
- `offset` (default: 0): Pagination offset

**Example Request**:
```bash
curl "http://localhost:8000/api/timeline/author/johndoe?platforms=twitter,youtube"
```

## Architecture

### Module Structure
```
research/backend/aggregation/
├── __init__.py              # Module exports
├── unified_timeline.py      # Core aggregation logic
└── README.md               # This file
```

### Key Components

#### UnifiedTimeline Class
Main aggregator class with methods:
- `get_timeline()` - Unified multi-platform timeline
- `get_platform_statistics()` - Platform statistics
- `filter_by_author()` - Author-filtered timeline
- `_deduplicate_items()` - Deduplication logic
- `_cosine_similarity()` - Similarity calculation

### Database Schema
Uses existing `sources` and `contents` tables:

**sources**:
- `id` (UUID)
- `platform` (varchar)
- `url` (text)
- `title` (text)
- `author` (varchar)
- `published_at` (timestamp)
- `scraped_at` (timestamp)
- `metadata` (jsonb)

**contents**:
- `id` (UUID)
- `source_id` (UUID, foreign key)
- `content_type` (varchar)
- `text_content` (text)
- `word_count` (int)
- `embedding` (vector[1536])
- `metadata` (jsonb)

## Deduplication Algorithm

1. **Embedding Comparison**: Uses pgvector cosine similarity
2. **Threshold**: Configurable similarity threshold (default: 0.85)
3. **Selection**: Keeps earliest published content when duplicates found
4. **Fallback**: Uses scraped_at if published_at is NULL
5. **No Embedding**: Items without embeddings are always kept

## Performance Considerations

- **Pagination**: Queries are paginated to limit memory usage
- **Deduplication Overhead**: When enabled, fetches 3x limit to ensure enough results after deduplication
- **Index Usage**: Uses existing indices on `platform`, `published_at`, `scraped_at`
- **Embedding Calculation**: Cosine similarity computed in Python (not database)

## Future Enhancements

- [ ] Database-side deduplication using pgvector distance operators
- [ ] Caching for frequently requested timelines
- [ ] Real-time updates via WebSocket
- [ ] Advanced filtering (date ranges, keywords, engagement metrics)
- [ ] Cross-platform conversation threading
- [ ] Duplicate detection without embeddings (fuzzy text matching)

## Testing

### Manual Testing
```bash
# Start the API server
cd research/backend
uvicorn main:app --reload

# Test timeline endpoint
curl "http://localhost:8000/api/timeline"

# Test with filters
curl "http://localhost:8000/api/timeline?platforms=twitter&limit=10"

# Test statistics
curl "http://localhost:8000/api/timeline/statistics"

# Test author filter
curl "http://localhost:8000/api/timeline/author/testuser"
```

### Integration with Frontend
The API is CORS-enabled for Writer module integration:
```javascript
// Fetch unified timeline
const response = await fetch('http://localhost:8000/api/timeline?platforms=twitter,youtube');
const data = await response.json();
console.log(`Found ${data.count} items from ${data.platforms.length} platforms`);
```

## Dependencies

- FastAPI - Web framework
- asyncpg - PostgreSQL async driver
- pgvector - Vector similarity extension
- Pydantic - Data validation

## Success Criteria

✅ **Single API endpoint returns combined results**
- `/api/timeline` endpoint operational
- Combines multiple platforms in response
- Returns unified data structure

✅ **Source filtering (show/hide platforms)**
- `platforms` query parameter functional
- Filters results by specified platforms
- Defaults to all platforms if not specified

✅ **Deduplication (same content from multiple sources)**
- Embedding-based similarity detection
- Configurable similarity threshold
- Returns deduplicated count

## Related Issues

- **Issue #82**: CHI-2 Multi-Source Aggregation
- **Issue #39**: IOTA (dependency)

## Authors

- CHI-2 Agent
- Claude Code (implementation)

## License

Part of the Extrophi Ecosystem monorepo.
