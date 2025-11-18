# GitHub Issues for IAC-032 Unified Scraper

**Purpose**: Trackable issues for web team implementation
**Total Issues**: 16
**Estimated Total Effort**: 71-93 hours

---

## Quick Reference

| Tier | Issues | Priority | Total Hours |
|------|--------|----------|-------------|
| 1 | 3 | P1-Critical | 9-14h |
| 2 | 4 | P1-Critical | 18-22h |
| 3 | 2 | P2-High | 14-18h |
| 4 | 2 | P2-High | 9-11h |
| 5 | 3 | P2-High | 15-19h |
| 6 | 2 | P3-Medium | 6-9h |

---

## TIER 1: CORE INFRASTRUCTURE (CRITICAL PATH BLOCKERS)

### Issue #1: Set up Python Backend Project Structure

```bash
gh issue create \
  --title "TIER 1.1: Set up Python Backend Project Structure" \
  --label "P1-critical,backend,infrastructure,agent-alpha" \
  --body "$(cat <<'EOF'
## Component
Backend Infrastructure - Project Foundation

## Priority
**P1-CRITICAL** - Blocks all other backend work

## Effort Estimate
4-6 hours

## Dependencies
None (first issue)

## Description
Create the complete Python backend project structure using UV package manager. This includes all `__init__.py` files, `pyproject.toml` with dependencies, and the base directory structure that all other agents will build upon.

## Files to Create
- `backend/__init__.py`
- `backend/pyproject.toml` (UV dependencies: FastAPI, SQLAlchemy 2.0, psycopg2-binary, pgvector, Pydantic v2, redis, rq)
- `backend/db/__init__.py`
- `backend/scrapers/__init__.py`
- `backend/services/__init__.py`
- `backend/api/__init__.py`
- `backend/api/routes/__init__.py`
- `backend/api/middleware/__init__.py`
- `tests/__init__.py`
- `tests/conftest.py` (pytest fixtures)
- `pytest.ini`

## Acceptance Criteria
- [ ] All `__init__.py` files created with proper exports
- [ ] `pyproject.toml` includes all required dependencies
- [ ] `uv sync` or `pip install -e .` succeeds without errors
- [ ] `pytest --collect-only` finds test modules
- [ ] Project can be imported: `python -c "import backend"`
- [ ] Directory structure matches architecture spec

## Reference Documents
- `docs/agents/AGENT_ALPHA_PROMPT.md`
- `docs/pm/TECHNICAL_PROPOSAL.md` (Appendix A)
- `CLAUDE.md` (UV setup instructions)
EOF
)"
```

---

### Issue #2: Set up PostgreSQL Database + Schema

```bash
gh issue create \
  --title "TIER 1.2: Set up PostgreSQL Database + Schema with pgvector" \
  --label "P1-critical,database,infrastructure,agent-alpha" \
  --body "$(cat <<'EOF'
## Component
Database Infrastructure - PostgreSQL + pgvector

## Priority
**P1-CRITICAL** - Blocks all data persistence

## Effort Estimate
3-4 hours

## Dependencies
Issue #1 (project structure)

## Description
Set up PostgreSQL 16 with pgvector extension for vector similarity search. Create complete database schema with 4+ tables (contents, authors, patterns, frameworks), connection pooling with SQLAlchemy, and ORM models.

## Files to Create
- `backend/db/connection.py` (SQLAlchemy engine with QueuePool, 10 connections, 20 overflow)
- `backend/db/models.py` (SQLAlchemy ORM + Pydantic v2 schemas)
- `backend/db/schema.sql` (Full PostgreSQL schema with pgvector extension)
- `backend/db/queries.py` (Common SQL operations)

## Database Schema Requirements
- `contents` table with vector(1536) for embeddings
- `authors` table with metrics tracking
- `patterns` table for cross-platform detection
- `frameworks` table (AIDA, PAS, BAB, PASTOR)
- IVFFlat index for cosine similarity search
- JSONB columns for flexible metadata
- UUID primary keys
- Automatic triggers for stats updates

## Acceptance Criteria
- [ ] PostgreSQL 16 running locally
- [ ] pgvector extension enabled: `CREATE EXTENSION vector;`
- [ ] All tables created: `psql unified_scraper -c "\dt"` shows 4+ tables
- [ ] Connection pooling functional
- [ ] Vector similarity query < 500ms: `SELECT * FROM contents ORDER BY embedding <=> '[...]' LIMIT 10;`
- [ ] Can INSERT 100 test rows in < 1 second
- [ ] ORM models correctly map to schema
- [ ] Pydantic schemas validate input/output

## Reference Documents
- `docs/agents/AGENT_ALPHA_PROMPT.md`
- `docs/pm/DATABASE_SCHEMA.md`
- `CLAUDE.md` (PostgreSQL schema section)
EOF
)"
```

---

### Issue #3: Create Base Scraper Module with Abstract Interface

```bash
gh issue create \
  --title "TIER 1.3: Create Base Scraper Module (BaseScraper ABC)" \
  --label "P1-critical,backend,architecture,agent-beta" \
  --body "$(cat <<'EOF'
## Component
Backend Scraper Core - Abstract Interface

## Priority
**P1-CRITICAL** - Blocks all platform-specific scrapers

## Effort Estimate
2-3 hours

## Dependencies
Issue #1 (project structure)

## Description
Create the BaseScraper abstract base class that all platform adapters must implement. Define the UnifiedContent schema and supporting models (AuthorModel, ContentModel, MetricsModel, AnalysisModel) that ensure data consistency across Twitter, YouTube, Reddit, and Web platforms.

## Files to Create
- `backend/scrapers/base.py` (BaseScraper ABC with health_check, extract, normalize methods)
- `backend/scrapers/models.py` (Pydantic schemas: UnifiedContent, AuthorModel, ContentModel, MetricsModel, AnalysisModel)

## BaseScraper Interface Contract
```python
from abc import ABC, abstractmethod
from typing import Literal

class BaseScraper(ABC):
    @abstractmethod
    async def health_check(self) -> dict:
        """Return scraper health status and metrics"""
        pass

    @abstractmethod
    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """Extract raw data from platform"""
        pass

    @abstractmethod
    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """Normalize raw data to UnifiedContent schema"""
        pass
```

## UnifiedContent Schema (from CLAUDE.md)
```python
class UnifiedContent(BaseModel):
    content_id: UUID
    platform: Literal["twitter", "youtube", "reddit", "amazon", "web"]
    source_url: str
    author: AuthorModel
    content: ContentModel
    metrics: MetricsModel
    analysis: AnalysisModel
    embedding: list[float]  # 1536 dims
    scraped_at: datetime
    metadata: dict[str, Any]
```

## Acceptance Criteria
- [ ] BaseScraper ABC defined with 3 abstract methods
- [ ] UnifiedContent Pydantic model validates correctly
- [ ] All supporting models (Author, Content, Metrics, Analysis) complete
- [ ] Can import: `from backend.scrapers.base import BaseScraper, UnifiedContent`
- [ ] Type hints complete for all models
- [ ] JSON serialization works: `content.model_dump_json()`

## Reference Documents
- `docs/agents/AGENT_BETA_PROMPT.md`
- `CLAUDE.md` (Unified Content Schema section)
EOF
)"
```

---

## TIER 2: SCRAPER MODULES (PARALLEL EXECUTION)

### Issue #4: Implement Twitter Scraper (Port IAC-024)

```bash
gh issue create \
  --title "TIER 2.1: Implement Twitter Scraper (Port IAC-024 Anti-Detection)" \
  --label "P1-critical,twitter,scraper,agent-beta" \
  --body "$(cat <<'EOF'
## Component
Twitter Platform Adapter

## Priority
**P1-CRITICAL** - Core scraping functionality

## Effort Estimate
6-8 hours

## Dependencies
Issues #1, #2, #3

## Description
Port the proven enterprise-grade Twitter scraping code from IAC-024 Tweet Hunter. This includes 1,765 lines of battle-tested anti-detection code with canvas fingerprint spoofing, human behavior simulation, and session health monitoring. **DO NOT write new code - reuse the proven implementation.**

## Source Code to Port
- `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py` (1,231 lines)
- `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/playwright_oauth_client.py` (534 lines)

## Files to Create
- `backend/scrapers/adapters/__init__.py`
- `backend/scrapers/adapters/twitter.py` (BaseScraper wrapper)
- `backend/scrapers/adapters/_persistent_x_session.py` (COPY from IAC-024)
- `backend/scrapers/adapters/_playwright_oauth.py` (COPY from IAC-024)
- `data/twitter_profiles/.gitkeep` (browser profile storage)

## Anti-Detection Features to Preserve
- Canvas fingerprint spoofing (imperceptible noise)
- WebGL fingerprint spoofing (common hardware IDs)
- Audio context fingerprinting (tiny processing variations)
- Human mouse movement (curved paths, 15-25 steps)
- Human typing patterns (WPM delays, punctuation pauses)
- Adaptive rate limiting (learns from success/failure)
- Session health monitoring (activity tracking, age limits)

## Dependencies to Add
- playwright
- playwright-stealth
- pyppeteer (fallback)

## Acceptance Criteria
- [ ] **CRITICAL**: Scrape 10 tweets from @dankoe without ban/rate limit
- [ ] All anti-detection features functional
- [ ] Session persists across process restarts
- [ ] Browser profile stored in `data/twitter_profiles/`
- [ ] Normalized to UnifiedContent schema
- [ ] Implements BaseScraper interface
- [ ] Health check returns session metrics
- [ ] OAuth fallback works if primary fails
- [ ] Data stored in PostgreSQL contents table

## Reference Documents
- `docs/agents/AGENT_BETA_PROMPT.md` (685 lines)
- `docs/pm/IAC024_PORTING_STRATEGY.md`
- IAC-024 source code (proven implementation)

## Critical Warning
**85% of naive Twitter scrapers get banned within minutes.** Use the proven IAC-024 code exactly as-is. Do not simplify or remove any anti-detection measures.
EOF
)"
```

---

### Issue #5: Implement YouTube Scraper

```bash
gh issue create \
  --title "TIER 2.2: Implement YouTube Scraper with Whisper Fallback" \
  --label "P1-critical,youtube,scraper,agent-gamma" \
  --body "$(cat <<'EOF'
## Component
YouTube Platform Adapter

## Priority
**P1-CRITICAL** - Core scraping functionality

## Effort Estimate
4-5 hours

## Dependencies
Issues #1, #2, #3

## Description
Extract YouTube video transcripts using youtube-transcript-api as primary method, with Whisper fallback for videos without captions. Extract rich metadata including title, channel, views, duration, published date, and tags.

## Files to Create
- `backend/scrapers/adapters/youtube.py` (BaseScraper implementation)
- `backend/scrapers/adapters/_youtube_transcript.py` (youtube-transcript-api wrapper)
- `backend/scrapers/adapters/_youtube_whisper.py` (Whisper fallback)
- `backend/scrapers/adapters/_youtube_metadata.py` (yt-dlp metadata extraction)

## Dependencies to Add
- youtube-transcript-api
- yt-dlp
- openai-whisper (for fallback)
- tiktoken

## Core Features
- Primary: youtube-transcript-api (fast, no download)
- Fallback: Whisper transcription (for videos without captions)
- Metadata: title, channel, views, duration, published_date, tags
- Channel video listing support
- Rate limiting (1 second between requests)

## Acceptance Criteria
- [ ] Extract transcript from video WITH captions
- [ ] Fallback to Whisper for videos WITHOUT captions
- [ ] All metadata captured (title, channel, views, duration, date)
- [ ] Normalized to UnifiedContent schema
- [ ] Implements BaseScraper interface
- [ ] Health check returns API status
- [ ] Data stored in PostgreSQL contents table
- [ ] Whisper model lazy-loaded (only when needed)
- [ ] API endpoint functional: `POST /scrape/youtube/{video_id}`

## Reference Documents
- `docs/agents/AGENT_GAMMA_PROMPT.md`
- `tools/yt-agent-app/youtube-ai-analyzer-prd.md` (627 lines Whisper patterns)
EOF
)"
```

---

### Issue #6: Implement Reddit Scraper

```bash
gh issue create \
  --title "TIER 2.3: Implement Reddit Scraper with PRAW" \
  --label "P1-critical,reddit,scraper,agent-delta" \
  --body "$(cat <<'EOF'
## Component
Reddit Platform Adapter

## Priority
**P1-CRITICAL** - Core scraping functionality

## Effort Estimate
4-5 hours

## Dependencies
Issues #1, #2, #3

## Description
Scrape Reddit posts and comments using PRAW (Python Reddit API Wrapper). Configure OAuth with FREE tier (1,000 req/10min), extract posts from subreddits with multiple sort methods, and preserve comment threading for VOC mining.

## Files to Create
- `backend/scrapers/adapters/reddit.py` (BaseScraper implementation)

## Dependencies to Add
- praw

## Environment Variables Required
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT=IAC032Scraper/1.0

## Core Features
- PRAW OAuth configuration
- Multiple sort methods: hot, new, top (with time filters)
- Comment extraction with depth control
- VOC mining: pain point and desire extraction
- Rate limit compliance (1,000 req/10min)

## VOC Mining Patterns
- Pain point indicators: low upvote ratio, help-seeking keywords ("struggle", "can't", "frustrated")
- Desire indicators: high scores, success keywords ("finally", "achieved", "breakthrough")

## Acceptance Criteria
- [ ] PRAW OAuth configured and authenticated
- [ ] Scrape 50 posts from r/productivity (hot sorting)
- [ ] Extract comments with threading preserved
- [ ] Respect rate limits (1,000 req/10min)
- [ ] VOC mining methods functional
- [ ] Normalized to UnifiedContent schema
- [ ] Implements BaseScraper interface
- [ ] Health check returns API status
- [ ] Data stored in PostgreSQL contents table

## Reference Documents
- `docs/agents/AGENT_DELTA_PROMPT.md`
EOF
)"
```

---

### Issue #7: Implement Web Scraper (Jina.ai FREE Tier)

```bash
gh issue create \
  --title "TIER 2.4: Implement Web Scraper with Jina.ai FREE Tier" \
  --label "P2-high,web,scraper,agent-epsilon" \
  --body "$(cat <<'EOF'
## Component
Web/Blog Platform Adapter

## Priority
**P2-HIGH** - Secondary scraping functionality

## Effort Estimate
3-4 hours

## Dependencies
Issues #1, #2, #3

## Description
Scrape static web content (blogs, documentation, articles) using Jina.ai Reader API FREE tier (50K pages/month). Automatic HTML to Markdown conversion. ScraperAPI fallback for JS-rendered pages if needed.

## Files to Create
- `backend/scrapers/adapters/web.py` (BaseScraper implementation)

## Dependencies to Add
- requests
- markitdown (fallback)

## Environment Variables
- JINA_API_KEY (optional, FREE tier works without)
- SCRAPERAPI_KEY (for fallback, $49/mo)

## Core Features
- Jina.ai Reader API: `https://r.jina.ai/{url}`
- Automatic HTML to Markdown conversion
- Metadata extraction (title, author, date, word_count)
- ScraperAPI fallback for JS-rendered pages
- Cost tracking and usage monitoring
- Known authority blog mapping (dankoe, jamesclear, calnewport)

## Cost Strategy
- Primary: Jina.ai FREE (50K pages/month, $0)
- Fallback: ScraperAPI ($49/mo if needed)
- Warning at 90% FREE tier usage

## Acceptance Criteria
- [ ] Jina.ai Reader API integration functional
- [ ] Scrape blog article (e.g., dankoe.com/blog/focus-systems)
- [ ] Convert HTML to clean Markdown
- [ ] Extract metadata (title, author, date)
- [ ] Normalized to UnifiedContent schema
- [ ] Implements BaseScraper interface
- [ ] ScraperAPI fallback for JS pages
- [ ] Cost tracking functional
- [ ] Data stored in PostgreSQL contents table

## Reference Documents
- `docs/agents/AGENT_EPSILON_PROMPT.md`
- `CLAUDE.md` (Jina.ai FREE tier section)
EOF
)"
```

---

## TIER 3: DATA PIPELINE

### Issue #8: Implement RAG Pipeline with ChromaDB

```bash
gh issue create \
  --title "TIER 3.1: Implement RAG Pipeline with ChromaDB + OpenAI Embeddings" \
  --label "P2-high,backend,rag,agent-zeta" \
  --body "$(cat <<'EOF'
## Component
Vector Database & Semantic Search

## Priority
**P2-HIGH** - Intelligence layer

## Effort Estimate
6-8 hours

## Dependencies
Issues #1-7 (needs scraped content to index)

## Description
Set up ChromaDB as local vector store with OpenAI embeddings (text-embedding-3-small, 1536 dimensions). Enable semantic search with cosine similarity, cross-platform pattern detection, and cost tracking.

## Files to Create
- `backend/services/embeddings.py` (OpenAI embedding generation with cost tracking)
- `backend/services/vector_store.py` (ChromaDB client with local persistence)
- `backend/services/rag_query.py` (Semantic search logic)
- `data/chromadb/` (persistent vector store directory)

## Dependencies to Add
- chromadb
- openai
- tiktoken

## Environment Variables
- OPENAI_API_KEY
- CHROMA_HOST=localhost
- CHROMA_PORT=8001

## Core Features
- OpenAI text-embedding-3-small (1536 dims)
- Batch embedding generation (100 items at a time)
- Cost tracking: $0.00002/1K tokens
- ChromaDB local persistence at `./data/chromadb`
- Cosine similarity search (> 0.7 relevance)
- Cross-platform pattern detection
- Context assembly for LLM queries

## Acceptance Criteria
- [ ] ChromaDB initialized with persistence
- [ ] OpenAI embeddings generating 1536-dim vectors
- [ ] Batch embed 100 items in < 10 seconds
- [ ] Semantic search: `query_similar("Dan Koe focus", limit=10)` returns relevant content
- [ ] Cost tracking functional with cumulative reporting
- [ ] Cross-platform pattern detection identifies elaboration
- [ ] API endpoint: `POST /query/rag` works with similarity > 0.7
- [ ] ChromaDB data persists across restarts

## Reference Documents
- `docs/agents/AGENT_ZETA_PROMPT.md`
- `docs/pm/DATABASE_SCHEMA.md` (embedding strategy)
EOF
)"
```

---

### Issue #9: Implement LLM Analysis Pipeline

```bash
gh issue create \
  --title "TIER 3.2: Implement LLM Analysis Pipeline (GPT-4 + Claude)" \
  --label "P2-high,backend,llm,agent-zeta" \
  --body "$(cat <<'EOF'
## Component
LLM Integration - Analysis & Generation

## Priority
**P2-HIGH** - Intelligence layer

## Effort Estimate
8-10 hours

## Dependencies
Issues #1, #8 (RAG pipeline)

## Description
Integrate GPT-4o-mini for bulk analysis (framework extraction, hook identification, pattern detection) and Claude Sonnet 4.5 for copywriting polish (course scripts, content briefs). Cost-optimized dual model strategy.

## Files to Create
- `backend/services/llm_service.py` (OpenAI and Anthropic client)
- `backend/services/analysis_service.py` (Framework extraction, pattern detection)
- `backend/prompts/` directory with analysis prompt templates

## Dependencies to Add
- openai
- anthropic

## Environment Variables
- OPENAI_API_KEY
- ANTHROPIC_API_KEY

## Dual Model Strategy
| Task | Model | Cost |
|------|-------|------|
| Bulk Analysis | GPT-4o-mini | $0.0015/1K tokens |
| Hook Extraction | GPT-4o-mini | $0.0015/1K tokens |
| Framework Detection | GPT-4o-mini | $0.0015/1K tokens |
| Copywriting Polish | Claude Sonnet 4.5 | $3/1M tokens |
| Course Script Gen | Claude Sonnet 4.5 | $3/1M tokens |

## Core Features
- Extract copywriting frameworks (AIDA, PAS, BAB, PASTOR)
- Identify hooks (curiosity, specificity, benefit-driven)
- Detect content patterns (cross-platform elaboration)
- Rank authorities by influence metrics
- Generate content briefs and course scripts
- Structured JSON output extraction

## Acceptance Criteria
- [ ] GPT-4o-mini API integration functional
- [ ] Claude Sonnet 4.5 API integration functional
- [ ] Framework extraction returns AIDA/PAS/BAB/PASTOR classification
- [ ] Hook identification categorizes hooks correctly
- [ ] Pattern detection finds cross-platform elaboration
- [ ] Authority ranking by engagement metrics
- [ ] Course script generation produces formatted output with citations
- [ ] Cost tracking for both models

## Reference Documents
- `docs/agents/AGENT_ZETA_PROMPT.md`
- `CLAUDE.md` (LLM Analysis Strategy section)
EOF
)"
```

---

## TIER 4: API ENDPOINTS

### Issue #10: Create FastAPI Scraping Endpoints

```bash
gh issue create \
  --title "TIER 4.1: Create FastAPI Scraping Endpoints" \
  --label "P2-high,backend,api,agent-eta" \
  --body "$(cat <<'EOF'
## Component
API Layer - Scraping Routes

## Priority
**P2-HIGH** - User-facing functionality

## Effort Estimate
5-6 hours

## Dependencies
Issues #4-7 (scraper modules)

## Description
Create FastAPI endpoints for all scraping operations. Implement scraper factory pattern for routing to correct adapter. Background task support for long-running scrapes.

## Files to Create
- `backend/main.py` (FastAPI app entry point)
- `backend/api/routes/scraping.py` (POST endpoints)
- `backend/services/scraper_factory.py` (platform routing)
- `backend/api/middleware/cors.py`
- `backend/api/middleware/errors.py`

## Endpoints to Create
- `POST /scrape/twitter/{username}` - Scrape Twitter account
- `POST /scrape/youtube/{video_id}` - Extract YouTube transcript
- `POST /scrape/reddit/{subreddit}` - Scrape subreddit
- `POST /scrape/web?url=...` - Scrape web page
- `GET /platforms` - List available platforms

## Request/Response Schema
```python
class ScrapeRequest(BaseModel):
    limit: int = 20
    include_comments: bool = False  # Reddit only

class ScrapeResponse(BaseModel):
    content_ids: list[UUID]
    count: int
    platform: str
    duration_seconds: float
```

## Acceptance Criteria
- [ ] All 4 scraping endpoints functional
- [ ] Scraper factory routes to correct adapter
- [ ] Return UnifiedContent IDs after scraping
- [ ] Error handling returns consistent JSON
- [ ] Background tasks for long scrapes
- [ ] CORS configured for frontend
- [ ] OpenAPI docs at /docs
- [ ] Rate limiting preparation (placeholder)

## Test Commands
```bash
curl -X POST http://localhost:8000/scrape/twitter/dankoe \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

curl -X POST http://localhost:8000/scrape/youtube/VIDEO_ID \
  -H "Content-Type: application/json"

curl -X POST http://localhost:8000/scrape/reddit/productivity \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

## Reference Documents
- `docs/agents/AGENT_ETA_PROMPT.md`
- `docs/pm/API_SPECIFICATIONS.md`
EOF
)"
```

---

### Issue #11: Create FastAPI RAG & Analysis Endpoints

```bash
gh issue create \
  --title "TIER 4.2: Create FastAPI RAG & Analysis Endpoints" \
  --label "P2-high,backend,api,agent-eta" \
  --body "$(cat <<'EOF'
## Component
API Layer - Intelligence Routes

## Priority
**P2-HIGH** - User-facing functionality

## Effort Estimate
4-5 hours

## Dependencies
Issues #8, #9 (RAG and LLM pipelines)

## Description
Create FastAPI endpoints for semantic search, pattern detection, course script generation, and markdown export. These endpoints leverage the RAG pipeline and LLM analysis services.

## Files to Create/Modify
- `backend/api/routes/query.py` (RAG search endpoints)
- `backend/api/routes/analysis.py` (pattern detection, generation)
- `backend/api/routes/health.py` (health checks)

## Endpoints to Create
- `POST /query/rag` - Semantic search
- `POST /analyze/patterns` - Cross-platform pattern detection
- `POST /generate/course-script` - Course script generation
- `GET /export/markdown` - Export research document
- `GET /health` - Service health check
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

## Request/Response Schema
```python
class RAGQuery(BaseModel):
    prompt: str
    limit: int = 10
    similarity_threshold: float = 0.7

class RAGResponse(BaseModel):
    results: list[UnifiedContent]
    query_time_ms: float
    total_matches: int

class CourseScriptRequest(BaseModel):
    topic: str
    audience: str
    format: str = "video course"
    length: str = "6 modules"
```

## Acceptance Criteria
- [ ] RAG query returns relevant content with similarity scores
- [ ] Pattern detection identifies cross-platform elaboration
- [ ] Course script generation produces formatted markdown with citations
- [ ] Export endpoint returns complete research document
- [ ] Health check returns service status (DB, Redis, ChromaDB)
- [ ] Response times < 200ms for non-LLM endpoints
- [ ] Error handling consistent across all endpoints

## Test Commands
```bash
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Dan Koe focus systems", "limit": 10}'

curl http://localhost:8000/health
```

## Reference Documents
- `docs/agents/AGENT_ETA_PROMPT.md`
- `docs/pm/API_SPECIFICATIONS.md`
EOF
)"
```

---

## TIER 5: TESTING & DEVOPS

### Issue #12: Set Up Comprehensive Test Suite

```bash
gh issue create \
  --title "TIER 5.1: Set Up Comprehensive Test Suite (80%+ Coverage)" \
  --label "P2-high,backend,testing" \
  --body "$(cat <<'EOF'
## Component
Testing Infrastructure

## Priority
**P2-HIGH** - Quality assurance

## Effort Estimate
8-10 hours

## Dependencies
Issues #1-11 (all backend code)

## Description
Create comprehensive test suite with unit tests, integration tests, and API endpoint tests. Target 80%+ code coverage. Mock external APIs for reliable testing.

## Files to Create
- `tests/conftest.py` (pytest fixtures, database setup)
- `tests/unit/test_scrapers.py`
- `tests/unit/test_models.py`
- `tests/unit/test_services.py`
- `tests/integration/test_database.py`
- `tests/integration/test_api.py`
- `tests/integration/test_scrapers_integration.py`
- `pytest.ini`

## Dependencies to Add
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock
- httpx (for FastAPI testing)
- vcr.py (API cassettes)

## Test Categories
- Unit tests: Individual functions, models, schemas
- Integration tests: Database operations, API flow
- Mock tests: External API responses (Twitter, YouTube, Reddit, OpenAI)
- Performance tests: Vector search latency, embedding generation speed

## Coverage Requirements
- 80%+ overall coverage
- 100% for critical paths (scrapers, RAG)
- Mock all external APIs
- Database fixtures for consistent test data

## Acceptance Criteria
- [ ] Pytest configured with async support
- [ ] 30+ unit tests passing
- [ ] 20+ integration tests passing
- [ ] All scrapers have mock tests
- [ ] Database fixtures for test isolation
- [ ] Coverage report generated: `pytest --cov=backend --cov-report=html`
- [ ] 80%+ code coverage achieved
- [ ] CI runs tests on every push
- [ ] No flaky tests

## Reference Documents
- `.github/workflows/ci.yml` (test job configuration)
- `docs/pm/TECHNICAL_PROPOSAL.md` (success criteria)
EOF
)"
```

---

### Issue #13: Create Docker/Podman Build Infrastructure

```bash
gh issue create \
  --title "TIER 5.2: Create Docker/Podman Build Infrastructure" \
  --label "P2-high,devops,docker" \
  --body "$(cat <<'EOF'
## Component
DevOps / Containerization

## Priority
**P2-HIGH** - Deployment infrastructure

## Effort Estimate
4-5 hours

## Dependencies
Issues #1-11 (backend code complete)

## Description
Create Dockerfiles for all services and podman-compose.yml for local orchestration. Enable single-command deployment to Hetzner VPS.

## Files to Create
- `backend/Dockerfile`
- `podman-compose.yml` (7 services: postgres, redis, chromadb, core_engine, twitter, youtube, reddit, web)
- `.dockerignore`
- `docker-entrypoint.sh` (initialization script)

## Container Services
1. **postgres** - pgvector/pgvector:pg16
2. **redis** - redis:7-alpine
3. **chromadb** - chromadb/chroma:latest
4. **core_engine** - FastAPI backend (custom build)
5. **twitter_scraper** - Twitter module (optional separate container)
6. **youtube_scraper** - YouTube module (optional)
7. **reddit_scraper** - Reddit module (optional)

## Podman Compose Requirements
- Health checks for all services
- Volume mounts for persistence (postgres_data, redis_data, chroma_data)
- Environment variable injection from .env
- Dependency ordering (postgres must be healthy before core_engine)
- Network configuration for inter-service communication

## Acceptance Criteria
- [ ] All Dockerfiles build successfully: `podman build -t unified_scraper_core ./backend`
- [ ] Container images run without errors
- [ ] `podman-compose up -d` brings up full stack
- [ ] Health checks pass for all services
- [ ] Data persists across restarts (volumes)
- [ ] Environment variables injected correctly
- [ ] CI builds all containers in pipeline

## Test Commands
```bash
podman-compose up -d
podman ps  # All containers running
curl http://localhost:8000/health  # Core engine healthy
podman-compose down
```

## Reference Documents
- `docs/pm/TECHNICAL_PROPOSAL.md` (Podman Compose configuration section)
- `CLAUDE.md` (Hetzner deployment strategy)
EOF
)"
```

---

### Issue #14: Configure Secrets Management & CI Automation

```bash
gh issue create \
  --title "TIER 5.3: Configure Secrets Management & CI Automation" \
  --label "P2-high,devops,ci-cd" \
  --body "$(cat <<'EOF'
## Component
CI/CD Pipeline - Security & Automation

## Priority
**P2-HIGH** - Production readiness

## Effort Estimate
3-4 hours

## Dependencies
Issues #12, #13 (tests and containers)

## Description
Configure GitHub Secrets for all API keys, set up branch protection rules, and finalize CI/CD pipeline automation. Enable automatic test enforcement and merge blocking.

## GitHub Secrets to Configure
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- SCRAPERAPI_KEY
- JINA_API_KEY
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- DATABASE_URL (for CI services)
- REDIS_URL (for CI services)
- CODECOV_TOKEN (optional)

## Files to Create/Modify
- `.secrets.baseline` (for detect-secrets)
- `.env.example` (template with all variables)
- `.github/workflows/ci.yml` (verify secrets usage)
- Branch protection rules (via GitHub UI or gh CLI)

## Branch Protection Configuration
```yaml
main:
  required_status_checks:
    strict: true
    contexts:
      - "Python Lint & Type Check"
      - "Python Unit Tests"
      - "Build Podman Containers"
      - "Integration Tests"
      - "Security Audit"
      - "All Checks Pass"
  required_pull_request_reviews:
    required_approving_review_count: 1
  enforce_admins: true
  allow_force_pushes: false
```

## Acceptance Criteria
- [ ] All secrets configured in GitHub repository settings
- [ ] CI uses secrets without logging them
- [ ] `.secrets.baseline` created for detect-secrets
- [ ] `.env.example` has all required variables
- [ ] Branch protection rules enabled on main
- [ ] Status checks required before merge
- [ ] Automatic PR comments on test failures
- [ ] Security audit blocks on vulnerabilities

## Reference Documents
- `.github/workflows/ci.yml`
- `docs/pm/TECHNICAL_PROPOSAL.md` (CI/CD Pipeline section)
- `docs/ci-setup/README.md`
EOF
)"
```

---

## TIER 6: DOCUMENTATION

### Issue #15: Update CI Configuration for Python Stack

```bash
gh issue create \
  --title "TIER 6.1: Update CI Configuration for Python Stack" \
  --label "P3-medium,devops,ci-cd" \
  --body "$(cat <<'EOF'
## Component
CI/CD Pipeline - Python Configuration

## Priority
**P3-MEDIUM** - Quality improvement

## Effort Estimate
2-3 hours

## Dependencies
Issues #1-14 (all implementation complete)

## Description
Fine-tune CI configuration to match actual implementation. Add pre-commit hooks for local linting, update coverage thresholds, and optimize pipeline performance.

## Files to Create/Modify
- `.pre-commit-config.yaml` (local git hooks)
- `pyproject.toml` (add tool configurations for black, isort, ruff, mypy)
- `.github/workflows/ci.yml` (optimize for actual structure)

## Pre-commit Hooks
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.0.280
    hooks:
      - id: ruff
```

## Acceptance Criteria
- [ ] Pre-commit hooks install: `pre-commit install`
- [ ] Hooks run on every commit
- [ ] CI matches local linting behavior
- [ ] Coverage threshold enforced (80%)
- [ ] Pipeline runs in < 25 minutes
- [ ] No false positives in security audit

## Reference Documents
- `.github/workflows/ci.yml`
- `docs/ci-setup/README.md`
EOF
)"
```

---

### Issue #16: Create API Documentation & Examples

```bash
gh issue create \
  --title "TIER 6.2: Create API Documentation & Examples" \
  --label "P3-medium,documentation" \
  --body "$(cat <<'EOF'
## Component
Documentation - API Reference

## Priority
**P3-MEDIUM** - User experience

## Effort Estimate
4-6 hours

## Dependencies
Issues #10, #11 (API endpoints)

## Description
Create comprehensive API documentation with Swagger enhancements, cURL examples for all endpoints, Python client library examples, and error code documentation.

## Files to Create
- `docs/api/README.md` (API overview)
- `docs/api/endpoints.md` (full endpoint reference)
- `docs/api/examples.md` (cURL and Python examples)
- `docs/api/errors.md` (error codes and troubleshooting)
- `backend/api/openapi_custom.py` (Swagger enhancements)

## Documentation Requirements
- OpenAPI spec enhancements (better descriptions, examples)
- cURL command for every endpoint
- Python code examples for common workflows
- Error response documentation
- Rate limiting documentation
- Authentication setup guide

## Example Workflows to Document
1. Scrape authority's Twitter → Index → Query similar content
2. Extract YouTube transcript → Analyze frameworks → Generate brief
3. Bulk Reddit scraping → VOC mining → Pattern detection
4. Full course script generation from multi-platform research

## Acceptance Criteria
- [ ] Swagger UI enhanced with examples at /docs
- [ ] cURL examples for all endpoints
- [ ] Python client examples work out of the box
- [ ] All error codes documented
- [ ] README links to documentation
- [ ] Examples tested and verified

## Reference Documents
- `docs/pm/API_SPECIFICATIONS.md`
- FastAPI auto-generated docs at /docs
EOF
)"
```

---

## BATCH CREATION SCRIPT

To create all 16 issues at once:

```bash
#!/bin/bash
# create_issues.sh

# TIER 1
gh issue create --title "TIER 1.1: Set up Python Backend Project Structure" --label "P1-critical,backend,infrastructure,agent-alpha" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 1.2: Set up PostgreSQL Database + Schema with pgvector" --label "P1-critical,database,infrastructure,agent-alpha" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 1.3: Create Base Scraper Module (BaseScraper ABC)" --label "P1-critical,backend,architecture,agent-beta" --body "See GITHUB_ISSUES_LIST.md for details"

# TIER 2
gh issue create --title "TIER 2.1: Implement Twitter Scraper (Port IAC-024 Anti-Detection)" --label "P1-critical,twitter,scraper,agent-beta" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 2.2: Implement YouTube Scraper with Whisper Fallback" --label "P1-critical,youtube,scraper,agent-gamma" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 2.3: Implement Reddit Scraper with PRAW" --label "P1-critical,reddit,scraper,agent-delta" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 2.4: Implement Web Scraper with Jina.ai FREE Tier" --label "P2-high,web,scraper,agent-epsilon" --body "See GITHUB_ISSUES_LIST.md for details"

# TIER 3
gh issue create --title "TIER 3.1: Implement RAG Pipeline with ChromaDB + OpenAI Embeddings" --label "P2-high,backend,rag,agent-zeta" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 3.2: Implement LLM Analysis Pipeline (GPT-4 + Claude)" --label "P2-high,backend,llm,agent-zeta" --body "See GITHUB_ISSUES_LIST.md for details"

# TIER 4
gh issue create --title "TIER 4.1: Create FastAPI Scraping Endpoints" --label "P2-high,backend,api,agent-eta" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 4.2: Create FastAPI RAG & Analysis Endpoints" --label "P2-high,backend,api,agent-eta" --body "See GITHUB_ISSUES_LIST.md for details"

# TIER 5
gh issue create --title "TIER 5.1: Set Up Comprehensive Test Suite (80%+ Coverage)" --label "P2-high,backend,testing" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 5.2: Create Docker/Podman Build Infrastructure" --label "P2-high,devops,docker" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 5.3: Configure Secrets Management & CI Automation" --label "P2-high,devops,ci-cd" --body "See GITHUB_ISSUES_LIST.md for details"

# TIER 6
gh issue create --title "TIER 6.1: Update CI Configuration for Python Stack" --label "P3-medium,devops,ci-cd" --body "See GITHUB_ISSUES_LIST.md for details"

gh issue create --title "TIER 6.2: Create API Documentation & Examples" --label "P3-medium,documentation" --body "See GITHUB_ISSUES_LIST.md for details"

echo "All 16 issues created successfully!"
```

---

## EXECUTION ORDER

1. **TIER 1** (Sequential) - Issues #1, #2, #3
2. **TIER 2** (Parallel after Tier 1) - Issues #4, #5, #6, #7
3. **TIER 3** (Parallel with Tier 2) - Issues #8, #9
4. **TIER 4** (After Tier 2-3) - Issues #10, #11
5. **TIER 5** (After Tier 4) - Issues #12, #13, #14
6. **TIER 6** (Anytime) - Issues #15, #16

**Total Estimated Time**: 71-93 hours (or ~6-7 hours with 7 parallel agents)
