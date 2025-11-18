# Research Module API Documentation

**Version:** 0.1.0
**Base URL:** `http://localhost:8000` (development)
**API Type:** REST
**Format:** JSON

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Scraping Endpoints](#scraping-endpoints)
  - [RAG Query Endpoints](#rag-query-endpoints)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)
- [Examples](#examples)

---

## Overview

The Research Module API provides content intelligence capabilities for the Extrophi Ecosystem. It enables:

- **Multi-platform scraping** (Twitter, YouTube, Reddit, Web)
- **Semantic search** via RAG (Retrieval Augmented Generation)
- **Content enrichment** with AI-powered suggestions
- **Pattern detection** across platforms

**Tech Stack:**
- FastAPI (Python 3.11+)
- PostgreSQL + pgvector (embeddings)
- ChromaDB (vector search)
- OpenAI GPT-4 (analysis)

---

## Authentication

**Current:** None (local development)
**Production:** API key via `X-API-Key` header (coming in v0.2.0)

```bash
# Future authentication example
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/scrape/twitter
```

---

## Endpoints

### Health Check

#### `GET /health`

Check API and service health status.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "postgresql://localhost:5432/research",
    "redis": "redis://localhost:6379/0",
    "chromadb": "chromadb:8000"
  }
}
```

**cURL Example:**
```bash
curl http://localhost:8000/health
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8000/health');
const health = await response.json();
console.log(health.status); // "healthy"
```

---

### Scraping Endpoints

#### `POST /scrape/{platform}`

Scrape content from a specific platform.

**Supported Platforms:**
- `twitter` - Twitter/X posts
- `youtube` - YouTube video transcripts
- `reddit` - Reddit posts and comments
- `web` - General web content

**Request Body:**
```json
{
  "target": "string",  // Platform-specific identifier
  "limit": 20          // Number of items to scrape (default: 20)
}
```

**Response:**
```json
{
  "status": "success",
  "platform": "twitter",
  "target": "@dankoe",
  "count": 20,
  "content_ids": [
    "uuid-1",
    "uuid-2",
    "..."
  ]
}
```

**cURL Examples:**

```bash
# Scrape Twitter posts
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "target": "@dankoe",
    "limit": 100
  }'

# Scrape YouTube transcript
curl -X POST http://localhost:8000/scrape/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dQw4w9WgXcQ",
    "limit": 1
  }'

# Scrape Reddit posts
curl -X POST http://localhost:8000/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "target": "r/productivity",
    "limit": 50
  }'

# Scrape web content
curl -X POST http://localhost:8000/scrape/web \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com/article",
    "limit": 1
  }'
```

**JavaScript Examples:**

```javascript
// Scrape Twitter
const scrapeTwitter = async (username, limit = 20) => {
  const response = await fetch('http://localhost:8000/scrape/twitter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target: username, limit })
  });
  return await response.json();
};

const result = await scrapeTwitter('@dankoe', 100);
console.log(`Scraped ${result.count} tweets`);

// Scrape YouTube
const scrapeYouTube = async (videoId) => {
  const response = await fetch('http://localhost:8000/scrape/youtube', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target: videoId, limit: 1 })
  });
  return await response.json();
};

const video = await scrapeYouTube('dQw4w9WgXcQ');
```

**Target Format by Platform:**

| Platform | Target Format | Example |
|----------|---------------|---------|
| Twitter  | `@username` or tweet URL | `@dankoe` or `https://twitter.com/dankoe/status/123` |
| YouTube  | Video ID or URL | `dQw4w9WgXcQ` or `https://youtube.com/watch?v=dQw4w9WgXcQ` |
| Reddit   | `r/subreddit` or post URL | `r/productivity` or `https://reddit.com/r/productivity/comments/abc123` |
| Web      | Full URL | `https://example.com/article` |

---

#### `GET /scrape/{platform}/health`

Check health status of a specific scraper.

**Response:**
```json
{
  "status": "ok",
  "platform": "twitter",
  "message": "Scraper operational"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/scrape/twitter/health
```

---

### RAG Query Endpoints

#### `POST /query/rag`

Perform semantic search across all scraped content.

**Request Body:**
```json
{
  "prompt": "string",           // Natural language query
  "n_results": 10,              // Number of results (default: 10)
  "platform_filter": "twitter", // Optional: filter by platform
  "author_filter": "@dankoe"    // Optional: filter by author
}
```

**Response:**
```json
{
  "query": "focus systems for knowledge workers",
  "count": 10,
  "results": [
    {
      "content_id": "uuid-1",
      "distance": 0.12,           // Lower = more similar
      "document": "Content text...",
      "metadata": {
        "platform": "twitter",
        "author_id": "@dankoe",
        "published_at": "2025-11-15T10:30:00Z",
        "engagement": {
          "likes": 1234,
          "retweets": 567
        }
      }
    }
  ]
}
```

**cURL Examples:**

```bash
# Basic semantic search
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "focus systems for knowledge workers",
    "n_results": 10
  }'

# Search with platform filter
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "copywriting frameworks",
    "n_results": 20,
    "platform_filter": "twitter"
  }'

# Search with author filter
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "building online courses",
    "n_results": 5,
    "author_filter": "@dankoe"
  }'
```

**JavaScript Examples:**

```javascript
// Basic semantic search
const searchContent = async (query, options = {}) => {
  const response = await fetch('http://localhost:8000/query/rag', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: query,
      n_results: options.limit || 10,
      platform_filter: options.platform,
      author_filter: options.author
    })
  });
  return await response.json();
};

// Usage examples
const results = await searchContent('focus systems');

const twitterResults = await searchContent('copywriting', {
  platform: 'twitter',
  limit: 20
});

const danKoeResults = await searchContent('courses', {
  author: '@dankoe'
});

// Process results
results.results.forEach(item => {
  console.log(`[${item.metadata.platform}] ${item.document}`);
  console.log(`Similarity: ${(1 - item.distance).toFixed(2)}`);
});
```

---

#### `GET /query/health`

Check vector store health status.

**Response:**
```json
{
  "status": "ok",
  "collections": 1,
  "total_documents": 1542
}
```

**cURL Example:**
```bash
curl http://localhost:8000/query/health
```

---

## Error Handling

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200  | Success | Request completed successfully |
| 400  | Bad Request | Invalid platform, missing required fields |
| 403  | Forbidden | Rate limit exceeded |
| 404  | Not Found | Content or endpoint not found |
| 500  | Internal Server Error | Database connection, scraper failure |
| 503  | Service Unavailable | Scraper unhealthy, service down |

### Error Examples

**Invalid Platform:**
```json
{
  "detail": "Invalid platform. Must be one of: ['twitter', 'youtube', 'reddit', 'web']"
}
```

**Scraper Unhealthy:**
```json
{
  "detail": "Scraper not healthy: Twitter API rate limit exceeded"
}
```

**Rate Limit Exceeded:**
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## Rate Limits

### Current Limits (Development)

**Per Endpoint:**
- `/scrape/*`: 10 requests/minute
- `/query/rag`: 60 requests/minute
- `/health`: Unlimited

### Platform-Specific Limits

**Twitter:**
- 100 tweets/request max
- 300 requests/15 minutes (Twitter API limit)

**YouTube:**
- 50 videos/request max
- No official limit (transcript API)

**Reddit:**
- 100 posts/request max
- 60 requests/minute (Reddit API limit)

**Web:**
- Depends on ScraperAPI plan (100K credits/month on $49 plan)

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1700000000
```

**Future Implementation** (v0.2.0)

---

## Examples

### Full Workflow: Scrape and Search

**1. Scrape Twitter Content**
```bash
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{"target": "@dankoe", "limit": 100}'
```

**2. Wait for Processing** (check health)
```bash
curl http://localhost:8000/health
```

**3. Search Semantically**
```bash
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "building online courses",
    "n_results": 5,
    "platform_filter": "twitter"
  }'
```

---

### JavaScript Integration Example

```javascript
class ResearchAPIClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async scrape(platform, target, limit = 20) {
    const response = await fetch(`${this.baseUrl}/scrape/${platform}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, limit })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    return await response.json();
  }

  async search(query, options = {}) {
    const response = await fetch(`${this.baseUrl}/query/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: query,
        n_results: options.limit || 10,
        platform_filter: options.platform,
        author_filter: options.author
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    return await response.json();
  }

  async health() {
    const response = await fetch(`${this.baseUrl}/health`);
    return await response.json();
  }
}

// Usage
const api = new ResearchAPIClient();

// Scrape and search
const scrapeResult = await api.scrape('twitter', '@dankoe', 100);
console.log(`Scraped ${scrapeResult.count} tweets`);

const searchResults = await api.search('copywriting frameworks', {
  platform: 'twitter',
  limit: 20
});

searchResults.results.forEach(result => {
  console.log(result.document);
});
```

---

## API Versioning

**Current Version:** `v0.1.0`
**Endpoint Prefix:** None (will be `/v1/` in production)

**Upcoming Changes (v0.2.0):**
- API key authentication
- Rate limit headers
- Webhook support for async scraping
- Batch scraping endpoints
- Export endpoints (markdown, JSON)

---

## OpenAPI Documentation

**Interactive Docs:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

**Explore the API visually** at `/docs` for request/response schemas, examples, and testing.

---

## Support

**Issues:** [GitHub Issues](https://github.com/iamcodio/IAC-033-extrophi-ecosystem/issues)
**Documentation:** `/research/docs/`
**Technical Proposal:** `/docs/pm/research/TECHNICAL-PROPOSAL-RESEARCH.md`

---

*Last Updated: 2025-11-18*
*Version: 0.1.0*
