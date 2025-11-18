# Integration Guide - IAC-032 Unified Scraper

This guide covers integration patterns for the Research module with other components of the Extrophi ecosystem.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Communication](#module-communication)
3. [Writer Module Integration](#writer-module-integration)
4. [Backend Module Integration](#backend-module-integration)
5. [Data Synchronization](#data-synchronization)
6. [Authentication Flows](#authentication-flows)
7. [Event-Driven Integration](#event-driven-integration)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Deployment Integration](#deployment-integration)

---

## Architecture Overview

The Research module (IAC-032 Unified Scraper) is part of the **IAC-033 Extrophi Ecosystem** monorepo and integrates with:

- **Writer Module** (`/writer/`) - BrainDump v3.0 voice journaling app
- **Backend Module** (`/backend/`) - Shared IAC-011 sovereign backend
- **Admin Module** (`/admin/`) - Project dashboard
- **Tools** (`/tools/`) - Shared utilities

### Module Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    IAC-033 Extrophi Ecosystem                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐   │
│  │   Writer     │◄────►│   Research   │◄────►│  Backend │   │
│  │ (BrainDump)  │      │  (Scraper)   │      │(IAC-011) │   │
│  └──────────────┘      └──────────────┘      └──────────┘   │
│         │                      │                    │         │
│         └──────────────────────┼────────────────────┘         │
│                                │                              │
│                         ┌──────▼──────┐                       │
│                         │   Admin     │                       │
│                         │ (Dashboard) │                       │
│                         └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Communication

### Communication Patterns

1. **REST API** - Primary method (HTTP/JSON)
2. **Shared Database** - PostgreSQL with unified schema
3. **Message Queue** - Redis for async jobs
4. **File System** - Markdown exports in shared directories

### Network Topology

**Development**:
```
Writer (localhost:1420) ──HTTP──> Research (localhost:8000) ──HTTP──> Backend (shared)
                                         │
                                         └──> PostgreSQL (localhost:5432)
                                         └──> Redis (localhost:6379)
                                         └──> ChromaDB (localhost:8000)
```

**Production** (Podman Compose):
```
Writer (Tauri App) ──HTTP──> Research (container: research-api:8000)
                                    │
                                    ├──> Backend (container: backend:8001)
                                    ├──> PostgreSQL (container: postgres:5432)
                                    ├──> Redis (container: redis:6379)
                                    └──> ChromaDB (container: chromadb:8000)
```

---

## Writer Module Integration

The Writer module (BrainDump v3.0) integrates with Research to enable **content research within the voice journaling workflow**.

### Use Case: Research-Enhanced Journaling

**Scenario**: User wants to journal about a topic and pull in related research.

**Flow**:

```mermaid
sequenceDiagram
    participant User
    participant Writer
    participant Research
    participant Backend

    User->>Writer: "Research focus systems for me"
    Writer->>Research: POST /query/rag {prompt: "focus systems"}
    Research->>Backend: Fetch embeddings
    Backend-->>Research: Return similar content
    Research-->>Writer: Return top 10 results
    Writer->>User: Display research sidebar
    User->>Writer: Insert citation into journal
    Writer->>Backend: Save journal entry with citation
```

### Integration Points

#### 1. RAG Query from Writer

**Writer (Tauri) → Research API**:

```rust
// src-tauri/src/research_client.rs
use reqwest;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct RAGQuery {
    prompt: String,
    n_results: u32,
    platform_filter: Option<String>,
}

#[derive(Deserialize)]
struct RAGResponse {
    results: Vec<RAGResult>,
    count: u32,
}

#[tauri::command]
async fn research_topic(prompt: String) -> Result<RAGResponse, String> {
    let client = reqwest::Client::new();

    let query = RAGQuery {
        prompt,
        n_results: 10,
        platform_filter: None,
    };

    let response = client
        .post("http://localhost:8000/query/rag")
        .json(&query)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let results: RAGResponse = response
        .json()
        .await
        .map_err(|e| e.to_string())?;

    Ok(results)
}
```

#### 2. Display Results in Writer UI

**Writer (Svelte 5) UI Component**:

```svelte
<!-- src/components/ResearchPanel.svelte -->
<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';

  let { query = $bindable('') } = $props();
  let results = $state([]);
  let loading = $state(false);

  async function searchResearch() {
    loading = true;
    try {
      results = await invoke('research_topic', { prompt: query });
    } catch (error) {
      console.error('Research failed:', error);
    } finally {
      loading = false;
    }
  }

  function insertCitation(result) {
    // Insert citation into journal entry
    const citation = `[${result.metadata.author_id}](${result.metadata.source_url})`;
    // Emit event to insert citation
    window.dispatchEvent(new CustomEvent('insert-citation', { detail: citation }));
  }
</script>

<div class="research-panel">
  <input bind:value={query} placeholder="Research a topic..." />
  <button onclick={searchResearch} disabled={loading}>
    {loading ? 'Searching...' : 'Search'}
  </button>

  {#if results.length > 0}
    <div class="results">
      {#each results as result}
        <div class="result-card">
          <p>{result.document}</p>
          <small>Distance: {result.distance.toFixed(3)}</small>
          <button onclick={() => insertCitation(result)}>Insert Citation</button>
        </div>
      {/each}
    </div>
  {/if}
</div>
```

#### 3. Environment Configuration

**Writer `.env`**:
```bash
# Research API endpoint
VITE_RESEARCH_API_URL=http://localhost:8000

# Optional: API key for production
VITE_RESEARCH_API_KEY=your_api_key_here
```

### Data Flow

1. User types research query in Writer
2. Writer calls Research `/query/rag` endpoint
3. Research returns semantically similar content
4. Writer displays results in sidebar
5. User selects content to insert as citation
6. Writer saves journal entry with citation metadata

---

## Backend Module Integration

The Research module uses the **shared Backend** (`/backend/`) for core services.

### Shared Components

#### 1. Database Layer

**Research** uses Backend's database models and connection:

```python
# backend/db/models.py - Shared models
from backend.db.models import ContentORM, AuthorORM, PatternORM

# Research uses these models directly
from backend.db.connection import get_session

@router.post("/scrape/{platform}")
async def scrape_platform(platform: str, db: Session = Depends(get_session)):
    # Use shared database session
    content = ContentORM(...)
    db.add(content)
    db.commit()
```

#### 2. Vector Store

**Research** uses Backend's ChromaDB client:

```python
# backend/vector/chromadb_client.py - Shared ChromaDB client
from backend.vector.chromadb_client import ChromaDBClient
from backend.vector.embeddings import EmbeddingGenerator

# Research uses for semantic search
chroma = ChromaDBClient()
results = chroma.query(query_embedding=embedding, n_results=10)
```

#### 3. Analysis Pipeline

**Research** uses Backend's LLM analyzer:

```python
# backend/analysis/analyzer.py - Shared analyzer
from backend.analysis.analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()
result = await analyzer.analyze_content(content)
```

### Integration Pattern

**Research Module** = Backend Core + Research-Specific Endpoints

```
┌─────────────────────────────────────┐
│       Research Module (FastAPI)     │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐  │
│  │   Research-Specific Routes    │  │
│  │   - /scrape/*                 │  │
│  │   - /query/*                  │  │
│  │   - /analyze/*                │  │
│  └─────────────┬─────────────────┘  │
│                │                     │
│  ┌─────────────▼─────────────────┐  │
│  │   Backend Core (Shared)       │  │
│  │   - Database (PostgreSQL)     │  │
│  │   - Vector Store (ChromaDB)   │  │
│  │   - Analysis (LLM)            │  │
│  │   - Queue (Redis)             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## Data Synchronization

### Unified Content Schema

All modules use the same content schema defined in `backend/db/models.py`:

```python
# Shared schema across all modules
class ContentORM(Base):
    __tablename__ = "contents"

    id = Column(UUID, primary_key=True)
    platform = Column(String(50))  # twitter, youtube, reddit, web
    source_url = Column(Text, unique=True)
    author_id = Column(String(255))
    content_body = Column(Text)
    metrics = Column(JSONB)
    analysis = Column(JSONB)
    embedding = Column(Vector(1536))
    scraped_at = Column(DateTime)
```

### Cross-Module Data Access

#### Writer Accessing Research Data

**Scenario**: Writer wants to display user's research history.

```python
# Writer backend query
from backend.db.connection import get_session
from backend.db.models import ContentORM

def get_research_history(user_id: str):
    session = get_session()
    contents = session.query(ContentORM)\
        .filter(ContentORM.metadata['user_id'] == user_id)\
        .order_by(ContentORM.scraped_at.desc())\
        .limit(20)\
        .all()
    return contents
```

#### Research Accessing Writer Data

**Scenario**: Research uses Writer's journal entries as additional context.

```python
# Research accessing Writer's data
from backend.db.models import ContentORM

def get_journal_context(user_id: str):
    session = get_session()
    journals = session.query(ContentORM)\
        .filter(ContentORM.platform == 'journal')\
        .filter(ContentORM.author_id == user_id)\
        .all()
    return journals
```

### Synchronization Strategy

**Real-time**: Direct database queries (current implementation)
**Future**: Event-driven sync via Redis pub/sub

```python
# Future: Event-driven sync
import redis

r = redis.Redis()

# Research publishes event when content is scraped
def publish_content_scraped(content_id: str):
    r.publish('content_scraped', json.dumps({
        'content_id': content_id,
        'platform': 'twitter',
        'timestamp': datetime.utcnow().isoformat()
    }))

# Writer subscribes to events
def subscribe_content_events():
    pubsub = r.pubsub()
    pubsub.subscribe('content_scraped')
    for message in pubsub.listen():
        # Update Writer UI with new content
        handle_new_content(message['data'])
```

---

## Authentication Flows

### Current State (Development)

**No authentication** - All endpoints are open.

### Future State (Production)

#### 1. API Key Authentication

**Research API validates API keys**:

```python
# backend/api/middleware/auth.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if not is_valid_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Usage in routes
@router.post("/scrape/twitter")
async def scrape_twitter(
    request: ScrapeRequest,
    api_key: str = Depends(verify_api_key)
):
    # Authenticated request
    pass
```

#### 2. OAuth for Platform Scrapers

**Twitter OAuth Flow**:

```mermaid
sequenceDiagram
    participant User
    participant Research
    participant Twitter

    User->>Research: Request Twitter scrape
    Research->>Twitter: OAuth request (via Playwright)
    Twitter-->>Research: Authorization code
    Research->>Twitter: Exchange code for token
    Twitter-->>Research: Access token
    Research->>Twitter: Scrape tweets with token
    Twitter-->>Research: Tweet data
    Research-->>User: Scraped content
```

**Implementation** (from IAC-024):

```python
# backend/scrapers/adapters/twitter.py
from playwright.async_api import async_playwright

class TwitterOAuthScraper:
    async def authenticate(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to Twitter OAuth
            await page.goto("https://twitter.com/i/oauth2/authorize?...")

            # Handle OAuth flow
            await page.click('button[data-testid="OAuth_Consent_Button"]')

            # Extract tokens from callback
            cookies = await context.cookies()
            self.save_session(cookies)
```

#### 3. User-Level Authentication

**Multi-user support**:

```python
# Each user has their own API key and data isolation
@router.post("/scrape/twitter")
async def scrape_twitter(
    request: ScrapeRequest,
    user_id: str = Depends(get_current_user)
):
    # Save content with user ownership
    content = ContentORM(
        ...,
        metadata={'user_id': user_id}
    )
```

---

## Event-Driven Integration

### Redis Pub/Sub for Async Communication

#### 1. Scraping Job Events

**Research publishes job status**:

```python
import redis
import json

r = redis.Redis(host='redis', port=6379)

# Publish job started
r.publish('scraping_jobs', json.dumps({
    'event': 'job_started',
    'job_id': job_id,
    'platform': 'twitter',
    'target': 'dankoe',
    'timestamp': datetime.utcnow().isoformat()
}))

# Publish job completed
r.publish('scraping_jobs', json.dumps({
    'event': 'job_completed',
    'job_id': job_id,
    'content_count': 100,
    'timestamp': datetime.utcnow().isoformat()
}))
```

**Admin Dashboard subscribes**:

```python
# admin/services/job_monitor.py
import redis

r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe('scraping_jobs')

for message in pubsub.listen():
    if message['type'] == 'message':
        event = json.loads(message['data'])

        if event['event'] == 'job_completed':
            # Update dashboard UI
            websocket.send_json({
                'type': 'job_completed',
                'data': event
            })
```

#### 2. Analysis Events

**Research publishes analysis complete**:

```python
r.publish('analysis_complete', json.dumps({
    'content_id': content_id,
    'frameworks': ['AIDA', 'PAS'],
    'hooks_count': 3,
    'timestamp': datetime.utcnow().isoformat()
}))
```

**Writer subscribes for real-time updates**:

```javascript
// Writer WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'analysis_complete') {
    // Update UI with analysis results
    updateAnalysisPanel(data.content_id, data.frameworks);
  }
};
```

---

## Error Handling & Retry Logic

### Retry Strategy

**Exponential Backoff**:

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def scrape_with_retry(platform: str, target: str):
    try:
        scraper = get_scraper(platform)
        return await scraper.extract(target)
    except Exception as e:
        print(f"Retry attempt failed: {e}")
        raise  # Will trigger retry
```

### Circuit Breaker

**Prevent cascading failures**:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api(url: str):
    response = await httpx.get(url)
    response.raise_for_status()
    return response.json()
```

### Error Propagation

**Research → Writer error flow**:

```rust
// Writer handles Research API errors
#[tauri::command]
async fn research_topic(prompt: String) -> Result<RAGResponse, String> {
    match call_research_api(prompt).await {
        Ok(response) => Ok(response),
        Err(e) if e.status() == 503 => {
            Err("Research service temporarily unavailable. Please try again.".to_string())
        },
        Err(e) if e.status() == 429 => {
            Err("Rate limit exceeded. Please wait before trying again.".to_string())
        },
        Err(e) => {
            Err(format!("Research failed: {}", e))
        }
    }
}
```

---

## Deployment Integration

### Podman Compose Setup

**`podman-compose.yml`** (Research + Backend + Dependencies):

```yaml
version: '3.8'

services:
  # PostgreSQL database (shared)
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: unified_scraper
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis (shared)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # ChromaDB (Research vector store)
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    environment:
      CHROMA_SERVER_HOST: 0.0.0.0
      CHROMA_SERVER_PORT: 8000

  # Research API
  research:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://scraper:${DB_PASSWORD}@postgres:5432/unified_scraper
      REDIS_URL: redis://redis:6379
      CHROMA_HOST: chromadb
      CHROMA_PORT: 8000
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
      - chromadb
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
```

### Container Networking

**Service Discovery**:

```python
# Containers can reference each other by service name
DATABASE_URL = "postgresql://scraper:password@postgres:5432/unified_scraper"
REDIS_URL = "redis://redis:6379"
CHROMA_HOST = "chromadb"  # Not localhost!
```

### Health Checks

**Docker health checks** for orchestration:

```yaml
services:
  research:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Scaling

**Horizontal scaling**:

```bash
# Scale Research API to 3 instances
podman-compose up --scale research=3

# Load balancer (Nginx) distributes requests
```

---

## Best Practices

### 1. Use Shared Models

Always import models from `backend/db/models.py`:

```python
# ✅ Good - Use shared models
from backend.db.models import ContentORM, AuthorORM

# ❌ Bad - Don't duplicate models
class ContentORM(Base):  # Don't do this!
    __tablename__ = "contents"
    ...
```

### 2. Consistent Error Handling

Use FastAPI's `HTTPException`:

```python
from fastapi import HTTPException

# Consistent error responses
raise HTTPException(
    status_code=400,
    detail="Invalid platform"
)
```

### 3. API Versioning

Prepare for future changes:

```python
# Current: /scrape/twitter
# Future: /v1/scrape/twitter, /v2/scrape/twitter

router = APIRouter(prefix="/v1")
```

### 4. Environment-Specific Config

```python
import os

# Development
if os.getenv("ENV") == "development":
    RESEARCH_API_URL = "http://localhost:8000"

# Production
else:
    RESEARCH_API_URL = "http://research:8000"
```

---

## Troubleshooting

### Common Integration Issues

#### 1. Connection Refused

**Problem**: Writer can't reach Research API

**Solution**:
```bash
# Check Research API is running
curl http://localhost:8000/health

# Check firewall rules
sudo ufw allow 8000

# Check Docker networking
podman network inspect extrophi_network
```

#### 2. Database Connection Failed

**Problem**: Research can't connect to PostgreSQL

**Solution**:
```bash
# Check DATABASE_URL is correct
echo $DATABASE_URL

# Test connection directly
psql $DATABASE_URL

# Check PostgreSQL is running
podman ps | grep postgres
```

#### 3. ChromaDB Not Found

**Problem**: Vector search fails

**Solution**:
```bash
# Check ChromaDB container
podman ps | grep chromadb

# Check ChromaDB health
curl http://chromadb:8000/api/v1/heartbeat

# Verify environment variables
echo $CHROMA_HOST
echo $CHROMA_PORT
```

---

## Next Steps

- [ ] Implement API key authentication
- [ ] Add WebSocket support for real-time updates
- [ ] Create SDK clients for Writer integration
- [ ] Add comprehensive integration tests
- [ ] Document webhook patterns
- [ ] Create monitoring dashboards

---

**Integration Guide Version**: 1.0
**Last Updated**: 2025-11-18
**Documentation**: Agent NU #40
