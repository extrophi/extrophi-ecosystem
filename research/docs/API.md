# API Documentation - IAC-032 Unified Scraper

**Base URL**: `http://localhost:8000` (development)
**API Version**: 0.1.0
**Framework**: FastAPI
**Interactive Docs**: http://localhost:8000/docs (Swagger UI)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health Check Endpoints](#health-check-endpoints)
3. [Scraping Endpoints](#scraping-endpoints)
4. [Query & RAG Endpoints](#query--rag-endpoints)
5. [Analysis Endpoints](#analysis-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limits](#rate-limits)

---

## Authentication

Currently, the API is open (no authentication required for development).

**Production Authentication** (coming soon):
```bash
curl -H "X-API-Key: your_api_key_here" \
     http://localhost:8000/scrape/twitter
```

---

## Health Check Endpoints

### GET /health

Check overall system health.

**Request**:
```bash
curl http://localhost:8000/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "services": {
    "database": "postgresql://scraper:***@postgres:5432/unified_scraper",
    "redis": "redis://redis:6379",
    "chromadb": "chromadb:8000"
  }
}
```

**Status Codes**:
- `200 OK` - All services healthy
- `503 Service Unavailable` - One or more services down

---

### GET /scrape/{platform}/health

Check platform-specific scraper health.

**Platforms**: `twitter`, `youtube`, `reddit`, `web`

**Request**:
```bash
curl http://localhost:8000/scrape/twitter/health
```

**Response** (200 OK):
```json
{
  "status": "ok",
  "platform": "twitter",
  "message": "Twitter scraper is ready"
}
```

---

### GET /query/health

Check vector store health.

**Request**:
```bash
curl http://localhost:8000/query/health
```

**Response**:
```json
{
  "status": "ok",
  "chroma_host": "chromadb",
  "chroma_port": "8000"
}
```

---

### GET /analyze/health

Check LLM analyzer health.

**Request**:
```bash
curl http://localhost:8000/analyze/health
```

**Response**:
```json
{
  "status": "ok",
  "provider": "openai",
  "model": "gpt-4"
}
```

---

## Scraping Endpoints

### POST /scrape/{platform}

Universal endpoint for scraping content from any platform.

**Platforms**: `twitter`, `youtube`, `reddit`, `web`

#### Twitter Scraping

**Request**:
```bash
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dankoe",
    "limit": 20
  }'
```

**Request Body**:
```json
{
  "target": "dankoe",  // Twitter username
  "limit": 20          // Number of tweets to scrape
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "platform": "twitter",
  "target": "dankoe",
  "count": 20,
  "content_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "..."
  ]
}
```

#### YouTube Scraping

**Request**:
```bash
curl -X POST http://localhost:8000/scrape/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dQw4w9WgXcQ",
    "limit": 1
  }'
```

**Request Body**:
```json
{
  "target": "dQw4w9WgXcQ",  // YouTube video ID or channel ID
  "limit": 1                // Number of videos to process
}
```

**Response**:
```json
{
  "status": "success",
  "platform": "youtube",
  "target": "dQw4w9WgXcQ",
  "count": 1,
  "content_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

#### Reddit Scraping

**Request**:
```bash
curl -X POST http://localhost:8000/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "target": "productivity",
    "limit": 50
  }'
```

**Request Body**:
```json
{
  "target": "productivity",  // Subreddit name (without r/)
  "limit": 50                // Number of posts to scrape
}
```

**Response**:
```json
{
  "status": "success",
  "platform": "reddit",
  "target": "productivity",
  "count": 50,
  "content_ids": ["uuid1", "uuid2", "..."]
}
```

#### Web Scraping

**Request**:
```bash
curl -X POST http://localhost:8000/scrape/web \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com/blog/post",
    "limit": 1
  }'
```

**Request Body**:
```json
{
  "target": "https://example.com/blog/post",  // Full URL
  "limit": 1
}
```

**Status Codes**:
- `200 OK` - Scraping successful
- `400 Bad Request` - Invalid platform or parameters
- `503 Service Unavailable` - Scraper not healthy
- `500 Internal Server Error` - Scraping failed

**Error Response**:
```json
{
  "detail": "Invalid platform. Must be one of: ['twitter', 'youtube', 'reddit', 'web']"
}
```

---

## Query & RAG Endpoints

### POST /query/rag

Semantic search across all scraped content using RAG (Retrieval Augmented Generation).

**Request**:
```bash
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What does Dan Koe say about focus systems?",
    "n_results": 10,
    "platform_filter": "twitter",
    "author_filter": "dankoe"
  }'
```

**Request Body**:
```json
{
  "prompt": "What does Dan Koe say about focus systems?",  // Natural language query
  "n_results": 10,                                         // Max results to return
  "platform_filter": "twitter",                            // Optional: filter by platform
  "author_filter": "dankoe"                                // Optional: filter by author
}
```

**Response** (200 OK):
```json
{
  "query": "What does Dan Koe say about focus systems?",
  "results": [
    {
      "content_id": "550e8400-e29b-41d4-a716-446655440000",
      "distance": 0.234,  // Lower = more similar (cosine distance)
      "document": "Your focus determines your reality. Here's how to build unbreakable focus systems...",
      "metadata": {
        "platform": "twitter",
        "author_id": "dankoe",
        "published_at": "2025-01-15T14:30:00Z",
        "source_url": "https://twitter.com/dankoe/status/123",
        "likes": 1234,
        "retweets": 456
      }
    },
    {
      "content_id": "550e8400-e29b-41d4-a716-446655440001",
      "distance": 0.287,
      "document": "Most people fail at focus because...",
      "metadata": {
        "platform": "twitter",
        "author_id": "dankoe",
        "published_at": "2025-01-14T10:15:00Z",
        "source_url": "https://twitter.com/dankoe/status/122",
        "likes": 892,
        "retweets": 234
      }
    }
  ],
  "count": 10
}
```

**Query Parameters**:
- `prompt` (required): Natural language search query
- `n_results` (optional, default=10): Number of results to return
- `platform_filter` (optional): Filter by platform (twitter, youtube, reddit, web)
- `author_filter` (optional): Filter by author username

**Status Codes**:
- `200 OK` - Query successful
- `500 Internal Server Error` - Query failed

---

## Analysis Endpoints

### POST /analyze/content

Analyze a single piece of content with LLM to extract frameworks, hooks, themes, and patterns.

**Request**:
```bash
curl -X POST http://localhost:8000/analyze/content \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your focus determines your reality. Most people fail because they try to do everything at once. Here is my 2-hour focus block system: 1. Deep work only 2. No distractions 3. Single task focus Thread below 👇"
  }'
```

**Request Body**:
```json
{
  "content": "Your focus determines your reality..."
}
```

**Response** (200 OK):
```json
{
  "frameworks": ["AIDA", "Thread Hook"],
  "hooks": [
    {
      "type": "curiosity",
      "text": "Your focus determines your reality"
    }
  ],
  "themes": ["focus", "productivity", "deep work"],
  "pain_points": ["trying to do everything at once", "distractions"],
  "key_insights": [
    "2-hour focus blocks are the solution",
    "Single task focus is essential"
  ],
  "sentiment": "positive",
  "tone": "authoritative",
  "call_to_action": "Thread below 👇"
}
```

**Analysis Types**:
- `frameworks`: Copywriting frameworks detected (AIDA, PAS, BAB, PASTOR)
- `hooks`: Hook types and text (curiosity, specificity, benefit)
- `themes`: Main topics and themes
- `pain_points`: Problems identified in content
- `key_insights`: Main takeaways
- `sentiment`: Overall sentiment (positive, negative, neutral, mixed)
- `tone`: Writing tone (authoritative, casual, humorous, professional)
- `call_to_action`: CTA identified

---

### POST /analyze/patterns

Detect patterns across multiple content pieces (e.g., cross-platform elaboration).

**Request**:
```bash
curl -X POST http://localhost:8000/analyze/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "content_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440001"
    ]
  }'
```

**Request Body**:
```json
{
  "content_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response** (200 OK):
```json
{
  "patterns": [
    {
      "type": "elaboration",
      "description": "Tweet concept expanded to YouTube video",
      "content_ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
      ],
      "confidence": 0.92,
      "temporal_gap_days": 7,
      "platforms": ["twitter", "youtube"]
    }
  ],
  "pattern_count": 1
}
```

**Pattern Types**:
- `elaboration`: Content expanded across platforms (tweet → blog → video)
- `repurposing`: Same content on multiple platforms
- `test_and_expand`: Viral content expanded into longer form
- `recurring_themes`: Themes repeated over time

---

## Error Handling

All endpoints return consistent error format:

**Error Response**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes**:

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid parameters or request format |
| 401 | Unauthorized | Invalid or missing API key (production) |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service is down or unhealthy |

**Example Errors**:

```json
// Invalid platform
{
  "detail": "Invalid platform. Must be one of: ['twitter', 'youtube', 'reddit', 'web']"
}

// Scraper not healthy
{
  "detail": "Scraper not healthy: Twitter API rate limit exceeded"
}

// Analysis failed
{
  "detail": "OpenAI API error: Invalid API key"
}
```

---

## Rate Limits

**Development**: No rate limits

**Production** (future):
| Tier | Requests/Hour | Scraping/Day | LLM Analysis/Day |
|------|---------------|--------------|------------------|
| Free | 100 | 10 jobs | 100 pieces |
| Basic | 1,000 | 100 jobs | 1,000 pieces |
| Pro | 10,000 | 1,000 jobs | 10,000 pieces |

**Rate Limit Headers** (coming soon):
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642521600
```

---

## Interactive Documentation

FastAPI provides automatic interactive API documentation:

**Swagger UI**: http://localhost:8000/docs
- Interactive testing interface
- Try all endpoints
- See request/response schemas

**ReDoc**: http://localhost:8000/redoc
- Clean, readable documentation
- OpenAPI schema viewer

---

## OpenAPI Schema

Download the full OpenAPI 3.0 schema:

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

Use this schema to:
- Generate client libraries
- Import into Postman
- Generate code stubs

---

## Examples

### Full Workflow Example

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Scrape Twitter content
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{"target": "dankoe", "limit": 100}'

# Response: {"status": "success", "count": 100, "content_ids": [...]}

# 3. Query with RAG
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "focus systems for creators",
    "n_results": 5,
    "author_filter": "dankoe"
  }'

# Response: {"query": "...", "results": [...], "count": 5}

# 4. Analyze content
curl -X POST http://localhost:8000/analyze/content \
  -H "Content-Type: application/json" \
  -d '{"content": "Your focus determines your reality..."}'

# Response: {"frameworks": ["AIDA"], "hooks": [...], ...}
```

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Scrape Twitter
response = requests.post(
    f"{BASE_URL}/scrape/twitter",
    json={"target": "dankoe", "limit": 20}
)
result = response.json()
print(f"Scraped {result['count']} tweets")

# RAG Query
response = requests.post(
    f"{BASE_URL}/query/rag",
    json={
        "prompt": "What does Dan Koe say about focus?",
        "n_results": 10,
        "platform_filter": "twitter"
    }
)
results = response.json()
for item in results["results"]:
    print(f"Distance: {item['distance']}")
    print(f"Content: {item['document'][:100]}...")
    print(f"URL: {item['metadata']['source_url']}\n")
```

### JavaScript/Node.js Example

```javascript
const BASE_URL = "http://localhost:8000";

// Scrape YouTube
const scrapeResponse = await fetch(`${BASE_URL}/scrape/youtube`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    target: "dQw4w9WgXcQ",
    limit: 1
  })
});

const scrapeResult = await scrapeResponse.json();
console.log(`Scraped ${scrapeResult.count} videos`);

// Analyze content
const analyzeResponse = await fetch(`${BASE_URL}/analyze/content`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    content: "Your focus determines your reality..."
  })
});

const analysis = await analyzeResponse.json();
console.log("Frameworks:", analysis.frameworks);
console.log("Hooks:", analysis.hooks);
```

---

## Next Steps

- **Authentication**: Implement API key authentication for production
- **Webhooks**: Add webhook support for async job completion
- **Batch Operations**: Support bulk scraping and analysis
- **Export Endpoints**: Add markdown/JSON/CSV export functionality
- **Pattern Detection**: Advanced cross-platform pattern detection
- **Course Generation**: Generate course scripts from research

---

**API Version**: 0.1.0
**Last Updated**: 2025-11-18
**Documentation**: Agent NU #40
