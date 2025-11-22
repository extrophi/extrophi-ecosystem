# Backend API - Demo Script
## Duration: 3 minutes
## Format: Teleprompter-style with timestamps

---

## [0:00-0:15] OPENING

Welcome to the Extrophi Backend API - the unified foundation that powers both Writer and Research, plus adds a novel attribution system with $EXTROPY token rewards.

Let me show you what makes this API special.

---

## [0:15-0:40] THE ARCHITECTURE

The Extrophi Backend is built with FastAPI - the modern Python framework known for speed, automatic documentation, and type safety.

[DEMONSTRATE: Show API documentation page]

Here's the interactive API documentation. Every endpoint is automatically documented with request schemas, response models, and a built-in testing interface.

This isn't an afterthought - it's generated directly from the code using Pydantic models.

The backend provides three main categories of endpoints:

**Scraping** - trigger and manage multi-platform content collection

**Querying** - semantic search and data retrieval

**Publishing** - content publication with attribution tracking

Let's walk through each one.

---

## [0:40-1:10] SCRAPING ENDPOINTS

First, the scraping API.

[DEMONSTRATE: POST /scrape/twitter]

I'll make a POST request to scrape a Twitter profile.

```json
POST /scrape/twitter
{
  "handle": "dankoe",
  "max_tweets": 100,
  "include_replies": false
}
```

The API responds immediately with a job ID - because scraping happens asynchronously in the background using Redis and RQ job queues.

[DEMONSTRATE: GET /scrape/status/{job_id}]

I can check the status with the job ID:

```json
GET /scrape/status/abc-123
{
  "status": "processing",
  "progress": 45,
  "total": 100,
  "platform": "twitter"
}
```

Once complete, the scraped data is automatically normalized into our unified schema, analyzed by LLM, embedded for semantic search, and stored in PostgreSQL with pgvector.

[DEMONSTRATE: Other scraping endpoints]

We also have endpoints for YouTube, Reddit, Amazon, and general web scraping - all following the same async pattern.

---

## [1:10-1:40] QUERY ENDPOINTS

Now let's talk about querying the intelligence we've gathered.

[DEMONSTRATE: POST /query/rag]

The RAG endpoint lets you search semantically across all platforms:

```json
POST /query/rag
{
  "prompt": "What do creators say about maintaining focus?",
  "platforms": ["twitter", "youtube", "reddit"],
  "limit": 10,
  "min_similarity": 0.8
}
```

The API returns semantically similar content ranked by cosine similarity - not just keyword matches.

[DEMONSTRATE: Response]

Look at this response - it includes content from all three platforms, with similarity scores, extracted frameworks, and source URLs.

[DEMONSTRATE: GET /query/patterns]

The patterns endpoint detects cross-platform elaboration:

```json
GET /query/patterns
{
  "author_id": "dankoe",
  "min_similarity": 0.85,
  "time_window_days": 14
}
```

This returns content clusters where the same idea appears across different platforms within a time window.

Perfect for reverse-engineering successful content strategies.

---

## [1:40-2:10] ANALYSIS ENDPOINTS

The analysis endpoints run LLM analysis on demand.

[DEMONSTRATE: POST /analyze/frameworks]

```json
POST /analyze/frameworks
{
  "content_ids": ["uuid1", "uuid2", "uuid3"],
  "frameworks": ["AIDA", "PAS", "BAB", "PASTOR"]
}
```

This batch-analyzes content to detect which copywriting frameworks are being used.

[DEMONSTRATE: POST /analyze/hooks]

The hooks endpoint extracts attention-grabbing openers:

```json
POST /analyze/hooks
{
  "content_ids": ["uuid1"],
  "hook_types": ["curiosity", "specificity", "benefit"]
}
```

Returns classified hooks with examples and effectiveness scores.

These endpoints use GPT-4 for bulk processing and Claude Sonnet for nuanced copywriting analysis - you configure which model to use based on your needs and budget.

---

## [2:10-2:40] ATTRIBUTION & PUBLISHING

Here's what makes Extrophi unique - the attribution system.

[DEMONSTRATE: POST /publish]

When you publish content created with Writer, you can track which research sources contributed:

```json
POST /publish
{
  "title": "The Focus System Guide",
  "content": "markdown content here",
  "attributions": [
    {"source_url": "twitter.com/dankoe/status/123", "contribution_type": "framework"},
    {"source_url": "youtube.com/watch?v=xyz", "contribution_type": "example"}
  ]
}
```

The API creates a publication record and distributes $EXTROPY tokens to attributed sources based on contribution type and value.

[DEMONSTRATE: GET /attributions/{publication_id}]

You can retrieve attribution data for any publication:

```json
GET /attributions/pub-456
{
  "publication_id": "pub-456",
  "total_attributions": 5,
  "extropy_distributed": 100,
  "top_contributors": [...]
}
```

This creates a value loop - better research leads to better content, which leads to recognition for original creators.

It's not cryptocurrency speculation - it's a reputation system acknowledging the knowledge creators who make your work possible.

---

## [2:40-2:50] AUTHENTICATION & API KEYS

All endpoints require authentication via API keys.

[DEMONSTRATE: GET /tokens/create]

Users can create and manage API keys through the tokens endpoints:

```json
POST /tokens/create
{
  "name": "My Integration",
  "permissions": ["read", "write", "scrape"]
}
```

Returns a secure API key that you include in request headers.

Keys can be scoped to specific permissions and revoked anytime.

---

## [2:50-3:00] CLOSING

The Extrophi Backend API - fast, documented, and built for extensibility.

Whether you're using Writer, Research, or building your own integration, the API gives you programmatic access to the full ecosystem.

Check the documentation at /docs for interactive exploration.

---

## PRODUCTION NOTES

**Screen Recording Sections:**
- 0:15-0:40: Show Swagger/ReDoc documentation interface
- 0:40-1:10: Use Postman/Insomnia to demonstrate scraping requests
- 1:10-1:40: Show RAG query with visual response (JSON formatted)
- 1:40-2:10: Demonstrate analysis endpoints with results
- 2:10-2:40: Show attribution flow (publish → attributions → rewards)
- 2:40-2:50: Display token creation and management

**Visual Overlays:**
- Highlight HTTP methods and status codes (POST, GET, 200, 202)
- Show request/response flow diagram
- Display async job queue visualization
- Illustrate semantic similarity with vector space diagram (optional)
- Show $EXTROPY token distribution flow

**Demo Preparation:**
- Have FastAPI server running locally
- Pre-load some sample data in database
- Prepare Postman collection with all requests
- Have authentication tokens ready (blur in recording)
- Set up example responses (formatted JSON)
- Create attribution example with real content

**Technical Details to Show:**
- Request headers (Authorization: Bearer <token>)
- Response status codes (200, 202, 404)
- Pagination in query results
- Error responses (show 4xx example)
- Rate limiting headers (if implemented)

**Code Examples:**
Show quick code snippets for common use cases:

```python
# Python example
import requests

headers = {"Authorization": f"Bearer {API_KEY}"}
response = requests.post(
    "http://localhost:8000/scrape/twitter",
    json={"handle": "dankoe", "max_tweets": 100},
    headers=headers
)
job_id = response.json()["job_id"]
```

```javascript
// JavaScript example
const response = await fetch('http://localhost:8000/query/rag', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: 'focus systems',
    platforms: ['twitter', 'youtube']
  })
});
const results = await response.json();
```

**Tone:** Technical but accessible. Assume audience has API experience but may not know this specific domain.

**Pacing:** Moderate. Give time to read request/response examples on screen.

**Key Messages:**
1. FastAPI = speed + automatic documentation + type safety
2. Async job processing for long-running scrapes
3. Semantic search via RAG/vector similarity
4. LLM analysis on demand (batch or real-time)
5. Attribution system creates value loop
6. RESTful, well-documented, easy to integrate
7. Secure authentication with scoped permissions
