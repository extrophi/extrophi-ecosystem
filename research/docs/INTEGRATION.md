# Research Module Integration Guide

**Version:** 0.1.0
**Audience:** Developers integrating Research API with Writer and Backend modules

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Module Communication](#module-communication)
- [Writer → Research Integration](#writer--research-integration)
- [Backend ↔ Research Database Sharing](#backend--research-database-sharing)
- [Environment Configuration](#environment-configuration)
- [Local Development Setup](#local-development-setup)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The Extrophi Ecosystem is a **monorepo** with three interconnected modules:

```
┌──────────────────────────────────────────────────────────┐
│                  Extrophi Ecosystem                       │
│                                                           │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│  │  Writer  │─────▶│ Research │◀─────│ Backend  │       │
│  │ (Tauri)  │ API  │ (FastAPI)│ DB   │(IAC-011) │       │
│  └──────────┘      └──────────┘      └──────────┘       │
│       │                  │                  │            │
│       │                  │                  │            │
│       ▼                  ▼                  ▼            │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│  │ SQLite   │      │PostgreSQL│◀─────│PostgreSQL│       │
│  │(Sessions)│      │ +pgvector│ Shared│(Unified) │       │
│  └──────────┘      └──────────┘      └──────────┘       │
│                          │                               │
│                          ▼                               │
│                    ┌──────────┐                          │
│                    │ ChromaDB │                          │
│                    │(Vectors) │                          │
│                    └──────────┘                          │
└──────────────────────────────────────────────────────────┘
```

**Key Integration Points:**

1. **Writer → Research**: HTTP API calls for content enrichment
2. **Research → Backend**: Shared PostgreSQL database for scraped content
3. **Research ↔ ChromaDB**: Vector embeddings for semantic search
4. **Research ↔ Redis**: Job queue for async scraping

---

## Module Communication

### Writer → Research Flow

**Use Case:** User writes in Writer, Research suggests related content

```
1. User types in Writer editor
2. Writer sends card content to Research API
3. Research generates embeddings
4. Research queries ChromaDB for similar content
5. Research returns suggestions to Writer
6. Writer displays suggestions in sidebar
```

**Request Flow:**

```mermaid
sequenceDiagram
    participant W as Writer (Tauri)
    participant R as Research API
    participant C as ChromaDB
    participant P as PostgreSQL

    W->>R: POST /api/enrich {content: "..."}
    R->>R: Generate embeddings
    R->>C: Query vectors (n_results=10)
    C-->>R: Similar content IDs
    R->>P: Fetch full content
    P-->>R: Content + metadata
    R-->>W: {suggestions: [...], sources: [...]}
    W->>W: Display in sidebar
```

### Backend ↔ Research Database Sharing

**Use Case:** Both modules access same scraped content

```
Backend Module:
  - Inserts scraped content into PostgreSQL
  - Manages schema migrations (Alembic)

Research Module:
  - Reads scraped content from PostgreSQL
  - Generates embeddings for ChromaDB
  - Performs semantic search
```

**Shared Database Schema:**

```sql
-- Located in: backend/db/schema.sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    platform VARCHAR(50),
    source_url TEXT UNIQUE,
    author_id VARCHAR(255),
    content_title TEXT,
    content_body TEXT,
    published_at TIMESTAMP,
    metrics JSONB,
    analysis JSONB,
    embedding vector(1536),
    scraped_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_platform ON contents(platform);
CREATE INDEX idx_author ON contents(author_id);
CREATE INDEX idx_embedding ON contents USING ivfflat (embedding vector_cosine_ops);
```

---

## Writer → Research Integration

### Tauri Command Setup (Writer Side)

**Location:** `writer/src-tauri/src/commands/research.rs`

```rust
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct EnrichRequest {
    pub content: String,
    pub n_results: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Suggestion {
    pub content_id: String,
    pub platform: String,
    pub snippet: String,
    pub author: String,
    pub url: String,
    pub similarity: f32,
}

#[tauri::command]
pub async fn enrich_content(content: String) -> Result<Vec<Suggestion>, String> {
    let client = Client::new();
    let research_url = std::env::var("RESEARCH_API_URL")
        .unwrap_or_else(|_| "http://localhost:8000".to_string());

    let response = client
        .post(format!("{}/query/rag", research_url))
        .json(&EnrichRequest {
            content,
            n_results: 10,
        })
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let data: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;

    // Parse suggestions from response
    let suggestions = parse_suggestions(&data)?;

    Ok(suggestions)
}
```

### Svelte Frontend Integration (Writer Side)

**Location:** `writer/src/components/ResearchSidebar.svelte`

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  interface Suggestion {
    content_id: string;
    platform: string;
    snippet: string;
    author: string;
    url: string;
    similarity: number;
  }

  let { content = $bindable('') } = $props();
  let suggestions = $state<Suggestion[]>([]);
  let loading = $state(false);

  async function fetchSuggestions() {
    if (!content || content.length < 50) return;

    loading = true;
    try {
      suggestions = await invoke<Suggestion[]>('enrich_content', { content });
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    } finally {
      loading = false;
    }
  }

  // Debounce content changes
  let timeoutId: number;
  $effect(() => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(fetchSuggestions, 1000);
  });
</script>

<div class="research-sidebar">
  <h3>Related Content</h3>

  {#if loading}
    <div class="loading">Searching...</div>
  {:else if suggestions.length > 0}
    <ul class="suggestions">
      {#each suggestions as suggestion}
        <li class="suggestion">
          <span class="platform">{suggestion.platform}</span>
          <p class="snippet">{suggestion.snippet}</p>
          <div class="meta">
            <span class="author">{suggestion.author}</span>
            <span class="similarity">{(suggestion.similarity * 100).toFixed(0)}% match</span>
          </div>
          <a href={suggestion.url} target="_blank">View original</a>
        </li>
      {/each}
    </ul>
  {:else}
    <div class="empty">No suggestions yet. Keep writing!</div>
  {/if}
</div>
```

### HTTP Client Integration (Alternative)

**For direct HTTP calls without Tauri command:**

```javascript
// writer/src/lib/api/research.js
export class ResearchAPIClient {
  constructor(baseUrl = import.meta.env.VITE_RESEARCH_API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async enrichContent(content, options = {}) {
    const response = await fetch(`${this.baseUrl}/query/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: content,
        n_results: options.limit || 10,
        platform_filter: options.platform,
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const data = await response.json();
    return this.transformResults(data.results);
  }

  transformResults(results) {
    return results.map(item => ({
      content_id: item.content_id,
      platform: item.metadata.platform,
      snippet: item.document.substring(0, 200) + '...',
      author: item.metadata.author_id,
      url: item.metadata.source_url,
      similarity: 1 - item.distance,
    }));
  }
}

// Usage in Svelte component
import { ResearchAPIClient } from '$lib/api/research';

const api = new ResearchAPIClient();
const suggestions = await api.enrichContent(content, { limit: 10 });
```

---

## Backend ↔ Research Database Sharing

### Connection Configuration

Both modules share the same PostgreSQL database but maintain separate connection pools.

**Backend Configuration:**

```python
# backend/db/connection.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/research")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Verify connections before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Research Module:**

Uses the **same database connection** but through different endpoints.

```python
# research/backend/db/connection.py
from backend.db.connection import engine, SessionLocal, get_session

# Reuse Backend's connection configuration
# No duplicate connection pool needed
```

### Schema Management

**Migrations are managed by Backend module only:**

```bash
# Backend module owns schema
cd backend

# Create new migration
alembic revision --autogenerate -m "Add embeddings column"

# Apply migrations
alembic upgrade head
```

**Research module is READ-ONLY for existing tables:**

```python
# research/backend/db/models.py
from backend.db.models import Content  # Import Backend's models

# Research can read but should not modify schema
```

### Data Flow

```
1. Backend scraper collects data
   ├─▶ Insert into PostgreSQL (contents table)
   └─▶ Trigger embedding generation

2. Research module listens for new content
   ├─▶ Generate OpenAI embeddings
   ├─▶ Update PostgreSQL (embedding column)
   └─▶ Index in ChromaDB

3. Writer queries Research
   └─▶ Research reads from PostgreSQL + ChromaDB
```

---

## Environment Configuration

### Environment Variables

Each module needs its own `.env` file with shared database credentials.

#### Writer Module (`writer/.env`)

```bash
# Research API connection
RESEARCH_API_URL=http://localhost:8000

# Optional: API key for production
RESEARCH_API_KEY=your-api-key
```

#### Research Module (`research/.env`)

```bash
# Database (shared with Backend)
DATABASE_URL=postgresql://user:password@localhost:5432/research

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Redis (job queue)
REDIS_URL=redis://localhost:6379/0

# OpenAI (embeddings + analysis)
OPENAI_API_KEY=sk-...

# Scrapers
TWITTER_USERNAME=your-twitter-username
TWITTER_PASSWORD=your-twitter-password
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
SCRAPER_API_KEY=your-scraperapi-key  # Optional
```

#### Backend Module (`backend/.env`)

```bash
# Database (same as Research)
DATABASE_URL=postgresql://user:password@localhost:5432/research

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
```

**Important:** All modules **MUST** use the same `DATABASE_URL` for shared database access.

---

## Local Development Setup

### Prerequisites

**System Requirements:**
- Python 3.11+ (installed via `uv`, NOT homebrew)
- Node.js 18+ (installed via `nvm`, NOT homebrew)
- PostgreSQL 16+ with pgvector extension
- Redis 7+
- ChromaDB (runs as service)

### Step 1: Install System Dependencies

```bash
# PostgreSQL with pgvector
brew install postgresql@16 pgvector

# Redis
brew install redis

# Start services
brew services start postgresql@16
brew services start redis
```

### Step 2: Setup Python Environment (Research Module)

```bash
cd research

# Create virtual environment with UV
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -e ../backend  # Install backend as editable dependency
uv pip install -r requirements.txt  # Research-specific deps
```

### Step 3: Setup Database

```bash
# Create database
createdb research

# Enable pgvector extension
psql research -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations (from Backend module)
cd ../backend
alembic upgrade head
```

### Step 4: Setup ChromaDB

```bash
# Option 1: Run as Docker container
docker run -d -p 8000:8000 chromadb/chroma

# Option 2: Run locally
cd research
source .venv/bin/activate
pip install chromadb
chroma run --path ./chroma_data --port 8000
```

### Step 5: Start Research API Server

```bash
cd research
source .venv/bin/activate

# Development mode with hot reload
uvicorn backend.main:app --reload --port 8000

# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 6: Start Writer (Optional)

```bash
cd writer
npm install
npm run tauri:dev
```

### Verification

**Check all services are running:**

```bash
# PostgreSQL
psql research -c "SELECT 1;"

# Redis
redis-cli ping

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Research API
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "database": "postgresql://localhost:5432/research",
#     "redis": "redis://localhost:6379/0",
#     "chromadb": "localhost:8000"
#   }
# }
```

---

## Troubleshooting

### Common Issues

#### 1. "Connection refused" to Research API

**Symptoms:**
```
Error: Failed to fetch suggestions
fetch error: Connection refused
```

**Solution:**
```bash
# Verify Research API is running
curl http://localhost:8000/health

# If not running, start it
cd research
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

#### 2. Database Connection Error

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Start if stopped
brew services start postgresql@16

# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### 3. pgvector Extension Not Found

**Symptoms:**
```
ERROR: type "vector" does not exist
```

**Solution:**
```bash
# Install pgvector
brew install pgvector

# Enable in database
psql research -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
psql research -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### 4. ChromaDB Connection Error

**Symptoms:**
```
httpx.ConnectError: [Errno 61] Connection refused
```

**Solution:**
```bash
# Check ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# If using Docker
docker ps | grep chroma

# Restart container
docker restart <container_id>

# If running locally
cd research
source .venv/bin/activate
chroma run --path ./chroma_data --port 8000
```

#### 5. Import Errors (Python Modules)

**Symptoms:**
```
ModuleNotFoundError: No module named 'backend'
```

**Solution:**
```bash
# Ensure UV virtual environment is activated
source .venv/bin/activate

# Install backend module as editable dependency
cd research
uv pip install -e ../backend

# Verify installation
python -c "import backend; print(backend.__file__)"
```

#### 6. Writer Cannot Connect to Research API

**Symptoms:**
```
Writer sidebar shows "Failed to fetch suggestions"
```

**Solution:**

**Check CORS configuration:**

```python
# backend/api/middleware/cors.py
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://localhost:5173"],  # Tauri + Vite
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

**Verify Tauri config:**

```json
// writer/src-tauri/tauri.conf.json
{
  "tauri": {
    "allowlist": {
      "http": {
        "scope": ["http://localhost:8000/*"]
      }
    }
  }
}
```

#### 7. Environment Variables Not Loaded

**Symptoms:**
```
KeyError: 'OPENAI_API_KEY'
```

**Solution:**

**Ensure `.env` files exist:**

```bash
# Research module
ls research/.env

# Backend module
ls backend/.env

# Writer module
ls writer/.env
```

**Load variables explicitly:**

```python
# research/backend/main.py
from dotenv import load_dotenv
import os

# Load .env before importing other modules
load_dotenv()

# Verify
print(os.getenv("OPENAI_API_KEY"))  # Should not be None
```

---

## Production Deployment Considerations

### Shared Database

**Use connection pooling to prevent exhaustion:**

```python
# backend/db/connection.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,       # Max connections per module
    max_overflow=20,    # Additional connections under load
    pool_timeout=30,    # Wait time before failing
    pool_recycle=3600,  # Recycle connections every hour
)
```

### API Gateway

**Route Writer → Research through API gateway:**

```
Writer → Nginx → Research API
```

**Example Nginx config:**

```nginx
# /etc/nginx/sites-available/research
upstream research_api {
    server localhost:8000;
    server localhost:8001;  # Multiple workers
}

server {
    listen 443 ssl;
    server_name api.extrophi.com;

    location /research/ {
        proxy_pass http://research_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment Separation

**Use different databases per environment:**

```bash
# Development
DATABASE_URL=postgresql://localhost:5432/research_dev

# Staging
DATABASE_URL=postgresql://staging-db:5432/research_staging

# Production
DATABASE_URL=postgresql://prod-db:5432/research_prod
```

---

## Next Steps

1. **Read API Documentation:** [API.md](./API.md)
2. **Review Technical Proposal:** `/docs/pm/research/TECHNICAL-PROPOSAL-RESEARCH.md`
3. **Check Research Module README:** [README.md](../README.md)
4. **Explore Backend Documentation:** `/backend/docs/`

---

*Last Updated: 2025-11-18*
*Version: 0.1.0*
