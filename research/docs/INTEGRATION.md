# Research Module Integration Guide

Complete integration documentation for connecting the Research Module with Writer (BrainDump), Backend services, and external systems.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Extrophi Ecosystem                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐         ┌──────────────┐      ┌─────────────┐ │
│  │   Writer    │ ◄─────► │   Research   │ ◄──► │   Backend   │ │
│  │ (BrainDump) │  CORS   │    Module    │ HTTP │  (Scraper)  │ │
│  │  Tauri App  │  HTTP   │   FastAPI    │      │   FastAPI   │ │
│  └─────────────┘         └──────────────┘      └─────────────┘ │
│         │                       │                      │         │
│         │                       ▼                      ▼         │
│         │              ┌──────────────┐      ┌──────────────┐   │
│         │              │  PostgreSQL  │      │  ChromaDB    │   │
│         │              │   + pgvector │      │   (Local)    │   │
│         │              └──────────────┘      └──────────────┘   │
│         │                       │                      │         │
│         └───────────────────────┴──────────────────────┘         │
│                        Shared Data Layer                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │  External APIs   │
                      │  - Twitter       │
                      │  - YouTube       │
                      │  - Reddit        │
                      │  - OpenAI        │
                      │  - ScraperAPI    │
                      └──────────────────┘
```

---

## Integration 1: Writer → Research

The Writer module (BrainDump v3.0) calls the Research Module API to enrich card content with suggestions from scraped data.

### Data Flow

```
┌────────────┐
│   Writer   │  User types in card editor
│   (Svelte) │
└─────┬──────┘
      │
      │ 1. User requests enrichment
      ▼
┌────────────┐
│  Research  │  POST /api/enrich
│    API     │  { card_id, content, context }
└─────┬──────┘
      │
      │ 2. Generate embedding from content
      ▼
┌────────────┐
│ PostgreSQL │  SELECT with pgvector similarity
│  pgvector  │  WHERE embedding <=> query_embedding < 0.2
└─────┬──────┘
      │
      │ 3. Return top suggestions
      ▼
┌────────────┐
│   Writer   │  Display suggestions in UI
│    UI      │  User accepts/rejects
└────────────┘
```

### Implementation

#### Writer Side (Svelte 5)

**File**: `writer/src/lib/services/research.ts`

```typescript
import { invoke } from '@tauri-apps/api/tauri';

interface EnrichmentRequest {
  card_id: string;
  content: string;
  context?: string;
  max_suggestions?: number;
}

interface Suggestion {
  text: string;
  type: 'fact' | 'example' | 'quote' | 'statistic';
  confidence: number;
  source?: {
    platform: string;
    url: string;
    author: string;
  };
}

interface EnrichmentResponse {
  card_id: string;
  suggestions: Suggestion[];
  sources: any[];
  processing_time_ms: number;
}

export async function enrichCard(
  cardId: string,
  content: string,
  context?: string
): Promise<EnrichmentResponse> {
  // Call Rust backend which proxies to Research API
  return await invoke<EnrichmentResponse>('enrich_card', {
    request: {
      card_id: cardId,
      content,
      context,
      max_suggestions: 5
    }
  });
}
```

#### Rust Backend (Tauri Command)

**File**: `writer/src-tauri/src/commands/research.rs`

```rust
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Serialize, Deserialize)]
pub struct EnrichRequest {
    card_id: String,
    content: String,
    context: Option<String>,
    max_suggestions: i32,
}

#[derive(Serialize, Deserialize)]
pub struct EnrichResponse {
    card_id: String,
    suggestions: Vec<Suggestion>,
    sources: Vec<Source>,
    processing_time_ms: f64,
}

#[tauri::command]
pub async fn enrich_card(
    request: EnrichRequest,
    app_state: State<'_, AppState>,
) -> Result<EnrichResponse, String> {
    let research_url = app_state.config.research_api_url.clone();
    let client = reqwest::Client::new();

    let response = client
        .post(format!("{}/api/enrich", research_url))
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to call Research API: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Research API error: {}", response.status()));
    }

    let enrichment = response
        .json::<EnrichResponse>()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(enrichment)
}
```

#### Configuration

**File**: `writer/src-tauri/tauri.conf.json`

```json
{
  "tauri": {
    "allowlist": {
      "http": {
        "scope": [
          "http://localhost:8000/*",
          "https://research.extrophi.com/*"
        ]
      }
    }
  }
}
```

**Environment Variables** (`writer/.env`):

```bash
RESEARCH_API_URL=http://localhost:8000
RESEARCH_API_TIMEOUT=5000
```

### CORS Configuration

**File**: `research/backend/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:1420",  # Tauri dev
        "tauri://localhost",      # Tauri prod
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Error Handling

**Writer Side**:

```typescript
try {
  const enrichment = await enrichCard(cardId, content);
  console.log(`Got ${enrichment.suggestions.length} suggestions`);
} catch (error) {
  console.error('Enrichment failed:', error);
  // Show user-friendly error message
  showToast('Failed to fetch suggestions. Please try again.', 'error');
}
```

**Research API**:

```python
from fastapi import HTTPException

@app.post("/api/enrich")
async def enrich_card(request: EnrichRequest):
    try:
        # Process enrichment
        return EnrichResponse(...)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
    except Exception as e:
        logger.error(f"Enrichment error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

---

## Integration 2: Backend ↔ Research

The Backend module provides scraping and analysis services that Research orchestrates.

### Data Flow

```
┌────────────┐
│  Research  │  User triggers scrape
│    API     │
└─────┬──────┘
      │
      │ 1. POST /api/scrape
      ▼
┌────────────┐
│  Backend   │  POST /scrape/{platform}
│  Scraper   │  { target, limit }
└─────┬──────┘
      │
      │ 2. Extract raw data
      ▼
┌────────────┐
│  Platform  │  Twitter/YouTube/Reddit API
│    APIs    │
└─────┬──────┘
      │
      │ 3. Normalize to UnifiedContent
      ▼
┌────────────┐
│ PostgreSQL │  INSERT INTO contents
│   + Redis  │  Queue for embedding generation
└─────┬──────┘
      │
      │ 4. Generate embeddings
      ▼
┌────────────┐
│  OpenAI    │  POST /v1/embeddings
│    API     │
└─────┬──────┘
      │
      │ 5. Store embeddings
      ▼
┌────────────┐
│  ChromaDB  │  collection.add(embeddings)
│   + PG     │  UPDATE contents SET embedding
└─────┬──────┘
      │
      │ 6. LLM Analysis
      ▼
┌────────────┐
│  Research  │  POST /analyze/content
│    API     │  Extract frameworks, hooks, themes
└────────────┘
```

### Shared Data Models

Both modules use the same `UnifiedContent` schema for consistency.

**File**: `backend/db/models.py` (shared)

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class AuthorModel(BaseModel):
    id: str
    platform: str
    username: str
    display_name: Optional[str] = None
    follower_count: Optional[str] = None
    authority_score: Optional[str] = None

class ContentModel(BaseModel):
    title: Optional[str] = None
    body: str
    word_count: int = 0

class MetricsModel(BaseModel):
    likes: int = 0
    retweets: int = 0
    views: int = 0
    engagement_rate: float = 0.0

class AnalysisModel(BaseModel):
    frameworks: List[str] = []
    hooks: List[str] = []
    themes: List[str] = []
    sentiment: str = "neutral"

class UnifiedContent(BaseModel):
    id: UUID
    platform: str
    source_url: str
    author: AuthorModel
    content: ContentModel
    metrics: MetricsModel
    analysis: Optional[AnalysisModel] = None
    embedding: Optional[List[float]] = None
    scraped_at: datetime
```

### Backend Implementation

#### Scraper Interface

**File**: `backend/scrapers/base.py`

```python
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    async def health_check(self) -> dict:
        """Check scraper connectivity"""
        pass

    @abstractmethod
    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """Extract raw platform-specific data"""
        pass

    @abstractmethod
    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """Normalize to UnifiedContent schema"""
        pass
```

#### Twitter Scraper Example

**File**: `backend/scrapers/adapters/twitter.py`

```python
from backend.scrapers.base import BaseScraper, UnifiedContent
import httpx

class TwitterScraper(BaseScraper):
    def __init__(self):
        self.api_url = "https://api.twitter.com/2"
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    async def health_check(self) -> dict:
        try:
            # Verify API credentials
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/users/me",
                    headers={"Authorization": f"Bearer {self.bearer_token}"}
                )
                response.raise_for_status()
            return {
                "status": "ok",
                "message": "Twitter API authenticated",
                "platform": "twitter"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "platform": "twitter"
            }

    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        # Implementation: Fetch tweets from @target
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/users/by/username/{target}",
                headers={"Authorization": f"Bearer {self.bearer_token}"}
            )
            user = response.json()["data"]

            response = await client.get(
                f"{self.api_url}/users/{user['id']}/tweets",
                params={"max_results": limit},
                headers={"Authorization": f"Bearer {self.bearer_token}"}
            )
            return response.json()["data"]

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        # Convert Twitter data to UnifiedContent
        return UnifiedContent(
            platform="twitter",
            source_url=f"https://twitter.com/user/status/{raw_data['id']}",
            author=AuthorModel(
                id=raw_data["author_id"],
                platform="twitter",
                username=raw_data["author"]["username"]
            ),
            content=ContentModel(
                body=raw_data["text"],
                word_count=len(raw_data["text"].split())
            ),
            metrics=MetricsModel(
                likes=raw_data["public_metrics"]["like_count"],
                retweets=raw_data["public_metrics"]["retweet_count"],
                views=raw_data["public_metrics"]["impression_count"]
            ),
            scraped_at=datetime.utcnow()
        )
```

#### Scraper Registry

**File**: `backend/scrapers/registry.py`

```python
from backend.scrapers.adapters.twitter import TwitterScraper
from backend.scrapers.adapters.youtube import YouTubeScraper
from backend.scrapers.adapters.reddit import RedditScraper
from backend.scrapers.adapters.web import WebScraper

SCRAPER_REGISTRY = {
    "twitter": TwitterScraper,
    "youtube": YouTubeScraper,
    "reddit": RedditScraper,
    "web": WebScraper,
}

def get_scraper(platform: str) -> BaseScraper:
    """Factory function to get platform scraper"""
    if platform not in SCRAPER_REGISTRY:
        raise ValueError(f"Unknown platform: {platform}")
    return SCRAPER_REGISTRY[platform]()
```

### Database Integration

#### PostgreSQL Schema

**File**: `backend/db/migrations/001_create_contents.sql`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Contents table
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    source_url TEXT UNIQUE NOT NULL,
    author_id VARCHAR(255) NOT NULL,
    content_title TEXT,
    content_body TEXT NOT NULL,
    published_at TIMESTAMP,
    metrics JSONB DEFAULT '{}'::jsonb,
    analysis JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536),  -- OpenAI embeddings
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    analyzed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indices for performance
CREATE INDEX idx_platform_author ON contents(platform, author_id);
CREATE INDEX idx_platform_published ON contents(platform, published_at);
CREATE INDEX idx_source_url ON contents(source_url);

-- Vector similarity index
CREATE INDEX idx_embedding_ivfflat ON contents
  USING ivfflat (embedding vector_cosine_ops);
```

#### Connection Management

**File**: `backend/db/connection.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@localhost:5432/unified_scraper"
)

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Vector Store Integration

#### ChromaDB Client

**File**: `backend/vector/chromadb_client.py`

```python
import chromadb
from chromadb.config import Settings

class ChromaDBClient:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_data"
        ))
        self.collection = self.client.get_or_create_collection(
            name="unified_content",
            metadata={"hnsw:space": "cosine"}
        )

    def add_content(self, content_id: str, embedding: list[float], metadata: dict):
        """Add content to vector store"""
        self.collection.add(
            ids=[content_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict = None
    ) -> dict:
        """Semantic search"""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

    def health_check(self) -> dict:
        try:
            count = self.collection.count()
            return {
                "status": "ok",
                "collection_count": count,
                "service": "chromadb"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "service": "chromadb"
            }
```

#### Embedding Generation

**File**: `backend/vector/embeddings.py`

```python
import openai
import os

class EmbeddingGenerator:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "text-embedding-ada-002"  # 1536 dims

    def generate(self, text: str) -> list[float]:
        """Generate embedding for text"""
        response = openai.Embedding.create(
            input=text,
            model=self.model
        )
        return response["data"][0]["embedding"]

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        response = openai.Embedding.create(
            input=texts,
            model=self.model
        )
        return [item["embedding"] for item in response["data"]]
```

### Analysis Pipeline

#### Content Analyzer

**File**: `backend/analysis/analyzer.py`

```python
import openai
from backend.analysis.prompts import FRAMEWORK_EXTRACTION_PROMPT

class ContentAnalyzer:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def analyze_content(self, content: str) -> dict:
        """Analyze single content piece"""
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": FRAMEWORK_EXTRACTION_PROMPT},
                {"role": "user", "content": content}
            ],
            temperature=0.3
        )

        # Parse structured response
        analysis = response.choices[0].message.content
        return self._parse_analysis(analysis)

    async def detect_patterns(self, content_list: list[dict]) -> dict:
        """Detect patterns across multiple pieces"""
        # Compare embeddings for similarity
        # Group by author and platform
        # Detect elaboration patterns (tweet → newsletter → video)
        pass

    def _parse_analysis(self, raw_analysis: str) -> dict:
        """Parse LLM response into structured data"""
        # Implementation details
        pass

    def health_check(self) -> dict:
        try:
            # Test OpenAI connection
            openai.Model.retrieve("gpt-4")
            return {"status": "ok", "service": "openai"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

---

## Integration 3: Job Queue System

For async scraping operations, the system uses Redis + Celery.

### Architecture

```
┌────────────┐
│  Research  │  POST /api/scrape
│    API     │  Returns job_id immediately
└─────┬──────┘
      │
      │ 1. Queue scraping job
      ▼
┌────────────┐
│   Redis    │  Job queue + status tracking
│   Queue    │
└─────┬──────┘
      │
      │ 2. Celery worker picks up job
      ▼
┌────────────┐
│   Celery   │  Execute scrape_content(platform, target)
│   Worker   │
└─────┬──────┘
      │
      │ 3. Call Backend scraper
      ▼
┌────────────┐
│  Backend   │  Extract → Normalize → Store
│  Scraper   │
└─────┬──────┘
      │
      │ 4. Update job status
      ▼
┌────────────┐
│   Redis    │  SET job:{job_id} status:completed
│   Store    │
└────────────┘
```

### Implementation

**File**: `backend/queue/celery_app.py`

```python
from celery import Celery
import os

celery_app = Celery(
    "research",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

**File**: `backend/queue/tasks.py`

```python
from backend.queue.celery_app import celery_app
from backend.scrapers import get_scraper

@celery_app.task(bind=True)
def scrape_content(self, platform: str, target: str, limit: int):
    """Async scraping task"""
    self.update_state(state="PROGRESS", meta={"progress": 0})

    try:
        scraper = get_scraper(platform)

        # Extract
        self.update_state(state="PROGRESS", meta={"progress": 33})
        raw_data = await scraper.extract(target, limit)

        # Normalize
        self.update_state(state="PROGRESS", meta={"progress": 66})
        content_ids = []
        for item in raw_data:
            normalized = await scraper.normalize(item)
            # Store in DB
            content_ids.append(str(normalized.id))

        # Generate embeddings
        self.update_state(state="PROGRESS", meta={"progress": 90})
        # ... embedding generation logic

        return {
            "status": "completed",
            "platform": platform,
            "target": target,
            "count": len(content_ids),
            "content_ids": content_ids
        }

    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
```

### Status Checking

**File**: `research/backend/main.py`

```python
from celery.result import AsyncResult

@app.get("/api/scrape/status/{job_id}")
async def check_scrape_status(job_id: str):
    """Check scraping job status"""
    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        return {
            "job_id": job_id,
            "status": "pending",
            "progress": 0
        }
    elif result.state == "PROGRESS":
        return {
            "job_id": job_id,
            "status": "processing",
            "progress": result.info.get("progress", 0)
        }
    elif result.state == "SUCCESS":
        return {
            "job_id": job_id,
            "status": "completed",
            "result": result.info
        }
    else:
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(result.info)
        }
```

---

## Integration 4: External APIs

### OpenAI Integration

**Environment**: Both modules

```python
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# Embeddings
response = openai.Embedding.create(
    input="Text to embed",
    model="text-embedding-ada-002"
)
embedding = response["data"][0]["embedding"]

# LLM Analysis
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Analyze this content..."}]
)
analysis = response.choices[0].message.content
```

### Platform APIs

#### Twitter (via IAC-024 patterns)

```python
# OAuth + Playwright for stealth scraping
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    # Implementation...
```

#### YouTube

```python
from youtube_transcript_api import YouTubeTranscriptApi

transcript = YouTubeTranscriptApi.get_transcript("video_id")
```

#### Reddit

```python
import praw

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="Extrophi Research v1.0"
)

subreddit = reddit.subreddit("productivity")
posts = subreddit.hot(limit=50)
```

---

## Deployment Considerations

### Service Discovery

Use environment variables for service URLs:

```bash
# Development
RESEARCH_API_URL=http://localhost:8000
BACKEND_API_URL=http://localhost:8001

# Production
RESEARCH_API_URL=https://research.extrophi.com
BACKEND_API_URL=https://api.extrophi.com
```

### Health Checks

Implement cascading health checks:

```python
@app.get("/health")
async def health_check():
    components = {
        "api": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "chromadb": await check_chromadb(),
        "scrapers": await check_scrapers()
    }

    overall_status = "healthy" if all(
        v == "healthy" for v in components.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "components": components
    }
```

### Monitoring

Log all integration points:

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/enrich")
async def enrich_card(request: EnrichRequest):
    logger.info(f"Enrichment request: card_id={request.card_id}")

    try:
        result = await process_enrichment(request)
        logger.info(f"Enrichment success: {len(result.suggestions)} suggestions")
        return result
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        raise
```

---

## Security Considerations

### API Key Management

```bash
# Never commit .env files
# Use environment variables or secret managers

# Development
OPENAI_API_KEY=sk-...
TWITTER_BEARER_TOKEN=...
REDDIT_CLIENT_SECRET=...

# Production (use secrets manager)
aws secretsmanager get-secret-value --secret-id prod/research/openai-key
```

### CORS Restrictions

```python
# Only allow known origins
allow_origins = [
    "http://localhost:5173",  # Dev only
    "https://app.extrophi.com"  # Production
]
```

### Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: "global")

@app.post("/api/enrich")
@limiter.limit("100/minute")
async def enrich_card(request: EnrichRequest):
    # Implementation
    pass
```

---

## Testing Integration

### Integration Test Example

**File**: `research/tests/integration/test_writer_integration.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_writer_enrich_flow():
    """Test full Writer → Research → Backend flow"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Enrich card
        response = await client.post("/api/enrich", json={
            "card_id": "test_card",
            "content": "Focus systems for knowledge workers",
            "max_suggestions": 3
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) <= 3
        assert data["card_id"] == "test_card"

        # 2. Verify suggestions have sources
        for suggestion in data["suggestions"]:
            assert suggestion["source"]["platform"] in [
                "twitter", "youtube", "reddit", "web"
            ]
            assert suggestion["confidence"] >= 0.0
            assert suggestion["confidence"] <= 1.0
```

---

## Troubleshooting

### Common Issues

#### 1. CORS Errors

**Symptom**: "CORS policy blocked" in browser console

**Solution**:
```python
# Add Writer origin to Research CORS config
allow_origins=[
    "http://localhost:5173",  # Your Vite dev server
    "tauri://localhost"       # Tauri app
]
```

#### 2. Connection Refused

**Symptom**: `Connection refused to localhost:8000`

**Solution**:
```bash
# Check Research API is running
curl http://localhost:8000/health

# Start if not running
cd research/backend
uvicorn main:app --reload --port 8000
```

#### 3. Slow Enrichment Responses

**Symptom**: Enrichment takes >5 seconds

**Solution**:
- Check PostgreSQL query performance
- Verify pgvector index exists
- Reduce `max_suggestions` parameter
- Cache frequent queries in Redis

#### 4. Embedding Generation Fails

**Symptom**: `openai.error.AuthenticationError`

**Solution**:
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Performance Optimization

### Caching Strategy

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@app.post("/api/enrich")
async def enrich_card(request: EnrichRequest):
    # Check cache first
    cache_key = f"enrich:{hash(request.content)}"
    cached = redis_client.get(cache_key)

    if cached:
        return EnrichResponse(**json.loads(cached))

    # Process enrichment
    result = await process_enrichment(request)

    # Cache for 1 hour
    redis_client.setex(
        cache_key,
        3600,
        json.dumps(result.dict())
    )

    return result
```

### Connection Pooling

```python
# PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# HTTP connections
httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100)
)
```

---

## Changelog

### v1.0.0 (2025-11-18)
- Initial integration documentation
- Writer → Research card enrichment flow
- Backend ↔ Research scraping pipeline
- Job queue system with Redis/Celery
- External API integrations
- Security and deployment guidelines

---

**Documentation Generated**: 2025-11-18
**Module**: Research (IAC-032 Unified Scraper)
**Integration Version**: 1.0.0
