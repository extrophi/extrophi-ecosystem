# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**IAC-032 Unified Scraper** is a multi-platform content intelligence engine that scrapes, analyzes, and synthesizes content from Twitter, YouTube, Reddit, Amazon, and other sources. It uses ScraperAPI.com for robust web scraping, RAG (Retrieval Augmented Generation) for semantic search, and LLM analysis to extract copywriting frameworks, identify authorities, detect content patterns, and generate production-ready content briefs and course scripts.

**NOT a code execution environment**: This is a **research and documentation project**. Code implementation happens upstream via CI/CD with Claude Code (web). This instance's role: **research → document → command**.

---

## Architecture Vision

### Core Stack (PRD_PROPER.md - Source of Truth)
- **Backend**: FastAPI + Python (UV package manager per parent CLAUDE.md)
- **Database**: PostgreSQL + pgvector (vector search for semantic queries)
- **RAG**: ChromaDB (local semantic search)
- **Scraping**: ScraperAPI.com ($49/mo primary) + platform-specific libraries
- **LLM**: OpenAI GPT-4 (bulk analysis) + Claude Sonnet 4.5 (copywriting polish)
- **Queue**: Redis + RQ (simple job orchestration)
- **Frontend** (Week 2): Tauri 2.0 + Svelte 5 (deferred from 3-day MVP)

### Platform Adapters (Modular Plugin System)
Each platform implements `BaseScraper` abstract class:
- **Twitter**: Reuse IAC-024 OAuth patterns (`/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/`)
  - `persistent_x_session.py` (1,231 lines - enterprise stealth)
  - `playwright_oauth_client.py` (534 lines - Google OAuth)
- **YouTube**: `youtube-transcript-api` + `yt-dlp`
- **Reddit**: PRAW (official API, 1,000 req/10min OAuth)
- **Amazon**: ScraperAPI structured endpoint (reviews extraction)
- **Web/Blogs**: ScraperAPI general endpoint
- **SERP**: ScraperAPI Google endpoint (SEO intelligence)

### Data Flow
```
Input: Project Brief ("Write about focus systems for knowledge workers")
  ↓
Intelligence Gathering: Scrape authorities (Dan Koe, Cal Newport, James Clear)
  ↓
Storage: PostgreSQL (structured) + ChromaDB (embeddings)
  ↓
Analysis: LLM extracts frameworks, hooks, pain points, patterns
  ↓
Output: Course scripts, blog outlines, tweet threads, content briefs
```

---

## Related Projects & Reusable Code

### IAC-024 Tweet Hunter (Production Twitter Scraping)
**Location**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/`

**Critical Files to Port**:
1. `src/scrapers/persistent_x_session.py` (1,231 lines)
   - Advanced fingerprint spoofing (canvas, WebGL, audio)
   - Human behavior simulation (curved mouse, typing variation)
   - Session health monitoring
   - Intelligent rate limiting (adaptive backoff)
   - **Port to**: `backend/scrapers/adapters/twitter.py`

2. `src/scrapers/playwright_oauth_client.py` (534 lines)
   - Google OAuth for @iamcodio account
   - Chrome profile persistence
   - Anti-detection measures
   - **Port to**: `backend/scrapers/adapters/twitter_oauth.py`

3. `src/database/schema.py`
   - SQLite CRUD patterns
   - **Adapt**: Add `platform` field for multi-platform schema

4. `src/models/tweet_models.py`
   - Tweet, User, Analysis Pydantic models
   - **Extend**: Create `UnifiedContent` schema

5. `src/api/main_playwright.py`
   - FastAPI structure, CORS, startup/shutdown hooks
   - **Adapt**: Multi-platform endpoints

**Why Reuse**: 100% proven code handling Twitter's aggressive bot detection. Already tested with @iamcodio account.

---

## Documentation Structure

### Primary Documents
1. **PRD_PROPER.md** (`docs/pm/`)
   - Authoritative PRD (Tauri + multi-platform scraper)
   - 772 lines, Day 1-3 implementation plan
   - Architecture: Tauri + Rust + Python modules
   - **Use this**, not PRD_v2.md

2. **PRD_v2.md** (`docs/pm/`)
   - Deprecated (PyQt + RAG focus)
   - Different scope (2TB course library indexing)
   - **Ignore for current sprint**

3. **Research Documents** (`docs/research/`)
   - `compass_artifact_wf-11cc96d9...` (634 lines)
     - Dan Koe methodology analysis
     - ScraperAPI vs Bright Data vs Apify comparison
     - RMBC copywriting framework automation
   - `compass_artifact_wf-1f5fcd14...` (317 lines)
     - Multi-platform scraping technical blueprint
     - Agentic architecture patterns
     - Vector database strategies

---

## Development Standards (From Parent CLAUDE.md)

### Environment Setup
```bash
# Python: Use UV (NOT homebrew)
uv venv
source .venv/bin/activate
uv pip install <package>

# Node.js: Use NVM (NOT homebrew)
nvm use 18

# Database: PostgreSQL with pgvector
brew install postgresql@16 pgvector
```

### Documentation Scraper Tool
**Location**: `tools/doc-scraper/`

**Purpose**: Scrapes documentation from ScraperAPI, Bright Data, Apify, Tauri, Svelte, etc.

**Usage**:
```bash
cd tools/doc-scraper
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml  # beautifulsoup4, markitdown, requests
python scrape_docs.py
```

**Output**: `docs/dev/{framework}/` (clean markdown files)

**Key File**: `scrape_docs.py` (215 lines)
- Configurable targets in `DOCS_TO_SCRAPE` dict
- Add new platforms by extending config
- Converts HTML → Markdown via `MarkItDown`

---

## 3-Day Sprint Architecture (PostgreSQL + API-First)

### Day 1: Backend Foundation + Twitter
**Deliverable**: Scrape 100 @dankoe tweets → PostgreSQL

**Tasks**:
1. Research ScraperAPI/Bright Data/Apify docs
2. PostgreSQL + pgvector setup
3. Port IAC-024 Twitter scrapers
4. Unified content schema (PostgreSQL + Pydantic)
5. FastAPI `/scrape/twitter/{username}` endpoint

### Day 2: Multi-Platform + RAG
**Deliverable**: RAG query "Dan Koe focus" returns Twitter+YouTube+Reddit

**Tasks**:
1. YouTube scraper (transcripts + metadata)
2. Reddit scraper (PRAW)
3. ScraperAPI web scraper (blogs)
4. ChromaDB integration (embeddings + indexing)
5. LLM analysis pipeline (GPT-4)

### Day 3: Intelligence Features
**Deliverable**: Project brief → course script with citations

**Tasks**:
1. Project brief parser
2. Authority detection (rank by influence)
3. Content gap analysis (SERP vs authorities)
4. Course script generator
5. Multi-format export (markdown, tweets, outlines)

---

## Unified Content Schema

```python
# PostgreSQL Schema
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    platform VARCHAR(50),  # 'twitter', 'youtube', 'reddit', 'amazon'
    source_url TEXT UNIQUE,
    author_id VARCHAR(255),
    content_title TEXT,
    content_body TEXT,
    published_at TIMESTAMP,
    metrics JSONB,  # likes, views, engagement
    analysis JSONB,  # frameworks, hooks, themes
    embedding vector(1536),  # OpenAI embeddings
    scraped_at TIMESTAMP,
    metadata JSONB
);

# Pydantic Model
class UnifiedContent(BaseModel):
    content_id: UUID
    platform: Literal["twitter", "youtube", "reddit", "amazon"]
    source_url: str
    author: AuthorModel
    content: ContentModel
    metrics: MetricsModel
    analysis: AnalysisModel
    embedding: List[float]  # 1536 dims
    scraped_at: datetime
    metadata: Dict[str, Any]
```

---

## ScraperAPI Integration Patterns

### Cost Structure
- **Hobby Plan**: $49/mo, 100K credits
- **Simple page**: $0.00049 (2,040 pages/$1)
- **JS-rendered**: $0.0024 (+5 credits, 417 pages/$1)
- **Structured endpoints**: Amazon, Google, eBay (same pricing)

### Usage Example
```python
import requests

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

# Simple scrape
params = {
    "api_key": SCRAPER_API_KEY,
    "url": "https://example.com",
    "render": "false"  # Set true for JS rendering (+5 credits)
}
response = requests.get("https://api.scraperapi.com", params=params)

# Amazon structured endpoint
params = {
    "api_key": SCRAPER_API_KEY,
    "url": "https://amazon.com/product/B08XYZ",
    "amazon_domain": "com",
    "type": "product"  # or "reviews", "search"
}
response = requests.get("https://api.scraperapi.com/structured/amazon/product", params=params)
data = response.json()  # Clean structured data
```

---

## Pattern Detection Algorithm

**Cross-Platform Elaboration** (Dan Koe's strategy):
1. Tweet concept (Tuesday)
2. Expand in newsletter (Saturday)
3. YouTube video (following week)

**Detection via Embeddings**:
```sql
-- Find similar content across platforms (cosine similarity > 0.85)
SELECT
    c1.platform as source,
    c2.platform as related,
    1 - (c1.embedding <=> c2.embedding) as similarity
FROM contents c1
JOIN contents c2 ON c1.author_id = c2.author_id
WHERE c1.platform != c2.platform
  AND 1 - (c1.embedding <=> c2.embedding) > 0.85
ORDER BY similarity DESC;
```

---

## LLM Analysis Strategy

### OpenAI GPT-4 (Bulk Processing)
- **Cost**: $0.0025/1K input, $0.01/1K output
- **Use for**: Framework extraction, hook identification, categorization
- **Volume**: High (100s of pieces per session)

### Claude Sonnet 4.5 (Copywriting Polish)
- **Cost**: $3/1M input, $15/1M output
- **Use for**: Final analysis, course script generation, nuanced copywriting
- **Volume**: Low (selected pieces only)

### Analysis Types
- **Hook Extraction**: Curiosity, specificity, benefit-driven
- **Framework Detection**: AIDA, PAS, BAB, PASTOR
- **VOC Mining**: Pain points (1-3 star), desires (5-star)
- **Pattern Recognition**: Cross-platform elaboration
- **Authority Ranking**: Follower count × engagement rate × content quality

---

## Course Creation Workflow

**Input**: Project brief
```json
{
  "topic": "focus systems for knowledge workers",
  "audience": "creators, entrepreneurs",
  "format": "video course (OBS + slides)",
  "length": "6 modules, 20 min each"
}
```

**Output**: Course script
```markdown
# Module 1: The Focus Crisis

## Hook (0:00-1:00)
[SLIDE: Productivity stats]
"You're not lazy. You're drowning in a system designed to distract."

## Problem (1:00-5:00)
[Based on Reddit r/productivity pain points]
- Average knowledge worker switches tasks every 3 minutes
- 23 minutes to regain deep focus after interruption
- [Quote from @dankoe tweet about focus]

## Framework (5:00-15:00)
[Dan Koe's 2-hour focus blocks]
...

## Citations
- Dan Koe tweet: [URL]
- Cal Newport blog: [URL]
- Reddit discussion: [URL]
```

---

## Development Workflow (Research → Document → Command)

### This Instance's Role (Claude Desktop)
1. **Research**: Scrape docs, analyze competitors, evaluate tools
2. **Document**: Architecture specs, API designs, decision matrices
3. **Command**: Create work packages for Claude Code (web) to execute

### Execution Environment (Claude Code Web)
- Runs actual code implementation
- Sets up databases, environments
- Deploys via CI/CD pipeline

### Deliverables from This Instance
1. `CLAUDE.md` (this file)
2. `NTFS.md` updates (session notes)
3. Architecture diagrams (Mermaid)
4. API specifications (OpenAPI/Swagger format)
5. Work packages (detailed instructions for web agents)
6. Decision matrices (ScraperAPI vs alternatives)
7. Platform adapter specifications

---

## Key Constraints

### 3-Day Timeline
- €900 budget expires in 3 days
- MVP focus: Backend API only (no desktop UI)
- Testing: cURL/Postman (no GUI for MVP)
- Week 2: Add Tauri + Svelte frontend

### Budget Allocation
- ScraperAPI: $49/mo (100K credits)
- OpenAI: ~$20/mo (bulk analysis)
- PostgreSQL: $0 (local or Hetzner VPS $4/mo)
- Redis: $0 (free tier)
- ChromaDB: $0 (local)
- **Total**: ~$69/mo

### Platform Priorities (Must-Have Day 3)
1. ✅ Twitter (reuse IAC-024)
2. ✅ YouTube (transcripts)
3. ✅ Reddit (PRAW)
4. 🔄 Amazon (stretch goal)

---

## GitHub Username
- **@iamcodio** (for PR creation, issue tracking)

---

## Success Criteria (Day 3 MVP)

**Backend API**:
- [ ] `/scrape/twitter/{username}` → 100 tweets stored
- [ ] `/scrape/youtube/{video_id}` → transcript + metadata
- [ ] `/scrape/reddit/{subreddit}` → 50 posts
- [ ] `/query/rag?prompt=...` → semantic search results
- [ ] `/analyze/patterns` → cross-platform elaboration detection
- [ ] `/generate/course-script` → production-ready script
- [ ] `/export/markdown` → formatted research document

**Data Quality**:
- [ ] PostgreSQL storing unified schema
- [ ] ChromaDB indexed with embeddings
- [ ] LLM analysis extracting frameworks
- [ ] Authority detection working
- [ ] Content gap analysis identifying opportunities

**Code Quality**:
- [ ] Modular adapter pattern (30 min to add platforms)
- [ ] Type-safe Pydantic models
- [ ] Clean separation: Frontend ← API ← Services ← Scrapers
- [ ] RQ queue for async scraping
- [ ] Proper error handling and retry logic

---

*Last updated: 2025-11-16*
*Project: IAC-032 Unified Scraper*
*Sprint: Day 1 of 3 (Research & Architecture)*
