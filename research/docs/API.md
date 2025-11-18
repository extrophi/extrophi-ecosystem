# Research Module API Reference

Complete API documentation for the Extrophi Research Module - a multi-platform content intelligence engine for scraping, analyzing, and enriching content.

## Base URLs

- **Research API**: `http://localhost:8000` (default)
- **Backend API**: `http://localhost:8001` (unified scraper backend)
- **Documentation**: `/docs` (OpenAPI/Swagger UI)
- **Health Check**: `/health`

## Authentication

Currently, the Research Module API does not require authentication for local development. Production deployments should implement API key authentication.

```bash
# Future: API key header (not yet implemented)
curl -H "X-API-Key: your_api_key" http://localhost:8000/health
```

---

## Research Module Endpoints

### Health Check

**GET** `/health`

Check service health and component status.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-18T10:30:00Z",
  "components": {
    "api": "healthy",
    "database": "pending",
    "embeddings": "pending",
    "scrapers": "pending"
  }
}
```

**cURL Example**:
```bash
curl http://localhost:8000/health
```

---

### Card Enrichment

**POST** `/api/enrich`

Enrich card content with suggestions from semantic search.

**Request Body**:
```json
{
  "card_id": "card_123",
  "content": "Focus systems help knowledge workers maintain deep work.",
  "context": "Previous card discussed productivity challenges.",
  "max_suggestions": 5
}
```

**Response**:
```json
{
  "card_id": "card_123",
  "suggestions": [
    {
      "text": "Cal Newport's Deep Work methodology emphasizes 2-hour focus blocks",
      "type": "example",
      "confidence": 0.85,
      "source": {
        "platform": "twitter",
        "url": "https://twitter.com/dankoe/status/123456",
        "title": "Focus systems thread",
        "author": "Dan Koe",
        "timestamp": "2025-11-15T08:00:00Z",
        "relevance_score": 0.85
      }
    }
  ],
  "sources": [
    {
      "platform": "twitter",
      "url": "https://twitter.com/dankoe/status/123456",
      "title": "Focus systems thread",
      "author": "Dan Koe",
      "timestamp": "2025-11-15T08:00:00Z",
      "relevance_score": 0.85
    }
  ],
  "processing_time_ms": 342.5,
  "timestamp": "2025-11-18T10:30:00Z"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": "card_123",
    "content": "Focus systems help knowledge workers maintain deep work.",
    "max_suggestions": 5
  }'
```

**Parameters**:
- `card_id` (string, required): Unique card identifier
- `content` (string, required): Card text to enrich
- `context` (string, optional): Additional context from surrounding cards
- `max_suggestions` (integer, optional): Max suggestions (1-20, default: 5)

**Error Responses**:
```json
{
  "detail": "Content is required and must not be empty"
}
```

---

### Trigger Scraping

**POST** `/api/scrape`

Initiate asynchronous content scraping job.

**Request Body**:
```json
{
  "url": "https://twitter.com/dankoe",
  "platform": "twitter",
  "depth": 1,
  "extract_embeddings": true
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "a3f8b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "status": "pending",
  "url": "https://twitter.com/dankoe",
  "estimated_time_seconds": 30,
  "message": "Scraping job queued. Platform: twitter, Depth: 1"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://twitter.com/dankoe",
    "platform": "twitter",
    "depth": 1,
    "extract_embeddings": true
  }'
```

**Parameters**:
- `url` (string, required): URL to scrape
- `platform` (string, optional): Platform hint (twitter, youtube, reddit, web)
- `depth` (integer, optional): Scraping depth (1-3, default: 1)
  - 1: Single page/profile
  - 2: Include related links
  - 3: Deep crawl
- `extract_embeddings` (boolean, optional): Generate embeddings (default: true)

**Supported Platforms**:
- `twitter` - Twitter/X profiles and threads
- `youtube` - YouTube videos (transcript + metadata)
- `reddit` - Reddit posts and threads
- `web` - Generic web pages and blogs

---

### Root Endpoint

**GET** `/`

API information and navigation.

**Response**:
```json
{
  "service": "Research Module API",
  "version": "1.0.0",
  "documentation": "/docs",
  "health": "/health",
  "endpoints": {
    "enrich": "POST /api/enrich",
    "scrape": "POST /api/scrape"
  }
}
```

---

## Backend Module Endpoints

### Scrape Platform Content

**POST** `/scrape/{platform}`

Scrape content from specified platform.

**Path Parameters**:
- `platform` (string, required): Platform name (twitter, youtube, reddit, web)

**Request Body**:
```json
{
  "target": "dankoe",
  "limit": 20
}
```

**Response**:
```json
{
  "status": "success",
  "platform": "twitter",
  "target": "dankoe",
  "count": 20,
  "content_ids": [
    "a3f8b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
    "b4g9c3d2-5e6f-7g8b-9c0d-1e2f3g4b5c6d"
  ]
}
```

**cURL Examples**:

```bash
# Twitter scraping
curl -X POST http://localhost:8001/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dankoe",
    "limit": 20
  }'

# YouTube scraping
curl -X POST http://localhost:8001/scrape/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dQw4w9WgXcQ",
    "limit": 1
  }'

# Reddit scraping
curl -X POST http://localhost:8001/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "target": "productivity",
    "limit": 50
  }'

# Web scraping
curl -X POST http://localhost:8001/scrape/web \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com/blog/post",
    "limit": 1
  }'
```

**Error Responses**:

```json
{
  "detail": "Invalid platform. Must be one of: ['twitter', 'youtube', 'reddit', 'web']"
}
```

```json
{
  "detail": "Scraper not healthy: Twitter API authentication failed"
}
```

---

### Scraper Health Check

**GET** `/scrape/{platform}/health`

Check specific scraper health status.

**Response**:
```json
{
  "status": "ok",
  "message": "Twitter scraper operational",
  "platform": "twitter",
  "timestamp": "2025-11-18T10:30:00Z"
}
```

**cURL Example**:
```bash
curl http://localhost:8001/scrape/twitter/health
```

---

### Analyze Content

**POST** `/analyze/content`

Analyze single content piece with LLM.

**Request Body**:
```json
{
  "content": "The 2-hour focus block is the foundation of deep work. No notifications, no meetings, just you and your craft."
}
```

**Response**:
```json
{
  "frameworks": ["BAB", "PAS"],
  "hooks": ["specificity", "benefit-driven"],
  "themes": ["productivity", "deep work", "focus"],
  "pain_points": ["notifications", "meetings", "interruptions"],
  "desires": ["deep work", "craftsmanship", "flow state"],
  "sentiment": "positive",
  "tone": "authoritative",
  "target_audience": "knowledge workers"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8001/analyze/content \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The 2-hour focus block is the foundation of deep work."
  }'
```

---

### Detect Patterns

**POST** `/analyze/patterns`

Detect patterns across multiple content pieces.

**Request Body**:
```json
{
  "content_ids": [
    "a3f8b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
    "b4g9c3d2-5e6f-7g8b-9c0d-1e2f3g4b5c6d"
  ]
}
```

**Response**:
```json
{
  "patterns": [
    {
      "type": "elaboration",
      "description": "Tweet → Newsletter → YouTube elaboration pattern",
      "confidence": 0.87,
      "content_ids": ["...", "..."],
      "timeline": {
        "twitter": "2025-11-15T08:00:00Z",
        "newsletter": "2025-11-18T10:00:00Z",
        "youtube": "2025-11-22T14:00:00Z"
      }
    }
  ],
  "recurring_themes": ["focus", "productivity", "deep work"],
  "common_frameworks": ["BAB", "PAS"]
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8001/analyze/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "content_ids": ["a3f8b2c1-...", "b4g9c3d2-..."]
  }'
```

---

### RAG Semantic Search

**POST** `/query/rag`

Perform semantic search across all scraped content.

**Request Body**:
```json
{
  "prompt": "How does Dan Koe approach focus and deep work?",
  "n_results": 10,
  "platform_filter": "twitter",
  "author_filter": "dankoe"
}
```

**Response**:
```json
{
  "query": "How does Dan Koe approach focus and deep work?",
  "results": [
    {
      "content_id": "a3f8b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "distance": 0.15,
      "document": "The 2-hour focus block is the foundation...",
      "metadata": {
        "platform": "twitter",
        "author_id": "dankoe",
        "published_at": "2025-11-15T08:00:00Z",
        "metrics": {
          "likes": 1240,
          "retweets": 89
        }
      }
    }
  ],
  "count": 10
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8001/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How does Dan Koe approach focus and deep work?",
    "n_results": 10,
    "platform_filter": "twitter"
  }'
```

**Parameters**:
- `prompt` (string, required): Natural language query
- `n_results` (integer, optional): Number of results (default: 10)
- `platform_filter` (string, optional): Filter by platform
- `author_filter` (string, optional): Filter by author ID

---

## Error Codes

All endpoints use standard HTTP status codes:

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 202 | Accepted | Async job queued |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Request body validation failed |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service/component unavailable |

**Validation Error Example**:
```json
{
  "detail": [
    {
      "loc": ["body", "content"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limits

Current implementation has no rate limits for local development. Production deployments should implement:

- **100 requests/minute** per IP for enrichment endpoints
- **20 scraping jobs/hour** per API key
- **1000 RAG queries/hour** per API key

---

## Data Models

### UnifiedContent Schema

```json
{
  "id": "a3f8b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "platform": "twitter",
  "source_url": "https://twitter.com/dankoe/status/123456",
  "author": {
    "id": "dankoe",
    "platform": "twitter",
    "username": "dankoe",
    "display_name": "Dan Koe",
    "follower_count": "500000",
    "authority_score": "0.95"
  },
  "content": {
    "title": null,
    "body": "The 2-hour focus block is the foundation of deep work.",
    "word_count": 10
  },
  "metrics": {
    "likes": 1240,
    "retweets": 89,
    "replies": 45,
    "views": 15000,
    "engagement_rate": 0.087
  },
  "analysis": {
    "frameworks": ["BAB"],
    "hooks": ["specificity"],
    "themes": ["productivity", "focus"],
    "sentiment": "positive",
    "tone": "authoritative"
  },
  "embedding": [0.023, -0.045, ...],
  "scraped_at": "2025-11-18T10:30:00Z",
  "analyzed_at": "2025-11-18T10:31:00Z"
}
```

---

## Integration Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

# Card enrichment
response = requests.post(
    f"{BASE_URL}/api/enrich",
    json={
        "card_id": "card_123",
        "content": "Focus systems help knowledge workers",
        "max_suggestions": 5
    }
)
enrichment = response.json()
print(f"Got {len(enrichment['suggestions'])} suggestions")

# Trigger scraping
response = requests.post(
    f"{BASE_URL}/api/scrape",
    json={
        "url": "https://twitter.com/dankoe",
        "platform": "twitter",
        "depth": 1
    }
)
job = response.json()
print(f"Job ID: {job['job_id']}")
```

### JavaScript Client

```javascript
const BASE_URL = "http://localhost:8000";

// Card enrichment
async function enrichCard(cardId, content) {
  const response = await fetch(`${BASE_URL}/api/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      card_id: cardId,
      content: content,
      max_suggestions: 5
    })
  });
  return await response.json();
}

// RAG query
async function searchContent(query) {
  const response = await fetch(`${BASE_URL}/query/rag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: query,
      n_results: 10
    })
  });
  return await response.json();
}
```

### Rust Client (Tauri)

```rust
use serde::{Deserialize, Serialize};
use reqwest;

#[derive(Serialize)]
struct EnrichRequest {
    card_id: String,
    content: String,
    max_suggestions: i32,
}

#[derive(Deserialize)]
struct EnrichResponse {
    card_id: String,
    suggestions: Vec<Suggestion>,
    processing_time_ms: f64,
}

async fn enrich_card(card_id: &str, content: &str) -> Result<EnrichResponse, reqwest::Error> {
    let client = reqwest::Client::new();
    let request = EnrichRequest {
        card_id: card_id.to_string(),
        content: content.to_string(),
        max_suggestions: 5,
    };

    let response = client
        .post("http://localhost:8000/api/enrich")
        .json(&request)
        .send()
        .await?
        .json::<EnrichResponse>()
        .await?;

    Ok(response)
}
```

---

## WebSocket Support (Future)

Real-time updates for scraping jobs (planned for v1.1):

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/scrape/job_id");

ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log(`Progress: ${status.progress}%`);
};
```

---

## Testing with Postman

Import the OpenAPI spec from `/docs` into Postman:

1. Open Postman
2. Import → Link: `http://localhost:8000/openapi.json`
3. Collection "Research Module API" will be created with all endpoints

---

## Environment Variables

```bash
# Research Module (.env)
OPENAI_API_KEY=sk-...
SCRAPER_API_KEY=...
DATABASE_URL=postgresql://user:pass@localhost:5432/research
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:5173,http://localhost:1420

# Backend Module
OPENAI_API_KEY=sk-...
JINA_API_KEY=...  # Optional, free tier
DATABASE_URL=postgresql://user:pass@localhost:5432/unified_scraper
```

---

## Changelog

### v1.0.0 (2025-11-18)
- Initial API release
- Card enrichment endpoint
- Scraping job queue
- Multi-platform scraping (Twitter, YouTube, Reddit, Web)
- RAG semantic search
- LLM analysis and pattern detection

---

**Documentation Generated**: 2025-11-18
**API Version**: 1.0.0
**Module**: Research (IAC-032 Unified Scraper)
