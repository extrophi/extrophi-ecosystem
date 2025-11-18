# IAC-032 Unified Scraper - Quick Start Guide

**Multi-platform content intelligence engine for content creators, copywriters, and marketers.**

Scrape Twitter, YouTube, Reddit, and web content, analyze with LLM to extract copywriting frameworks, detect cross-platform patterns, and generate production-ready content.

---

## Quick Start (5 Minutes)

### Prerequisites

- **Python 3.11+** installed
- **UV package manager** (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Docker/Podman** (for containerized deployment)
- **PostgreSQL 16** with pgvector extension
- **Redis** (for job queuing)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/Iamcodio/IAC-033-extrophi-ecosystem.git
cd IAC-033-extrophi-ecosystem/research
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment with UV
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies (from parent backend/)
cd ../backend
uv pip install -r requirements.txt
cd ../research
```

#### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables** (`.env`):

```bash
# Database (PostgreSQL)
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://scraper:${DB_PASSWORD}@localhost:5432/unified_scraper

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# OpenAI (for embeddings and GPT-4 analysis)
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic (for Claude Sonnet polish)
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here

# ScraperAPI (optional, fallback for JS-rendered pages)
SCRAPERAPI_KEY=your-scraperapi-key-here

# Jina.ai Reader API (FREE tier, 50K pages/month)
JINA_API_KEY=your-jina-key-here

# Reddit OAuth (FREE tier, 1000 req/10min)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=IAC032Scraper/1.0
```

#### 4. Start Dependencies (Podman Compose)

```bash
# Start PostgreSQL, Redis, ChromaDB
podman-compose up -d postgres redis chromadb

# OR with Docker
docker-compose up -d postgres redis chromadb
```

#### 5. Initialize Database

```bash
# Create database and tables
psql -U scraper -d unified_scraper -f backend/db/schema.sql

# OR use Python migration script (if available)
python -m backend.db.migrate
```

#### 6. Run the API Server

```bash
# From repository root
cd /path/to/extrophi-ecosystem

# Run FastAPI server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Server started at**: http://localhost:8000

**Interactive Docs**: http://localhost:8000/docs

---

## Basic Usage Examples

### 1. Health Check

Verify all services are running:

```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "postgresql://scraper:***@localhost:5432/unified_scraper",
    "redis": "redis://localhost:6379",
    "chromadb": "localhost:8000"
  }
}
```

---

### 2. Scrape Twitter Content

Scrape tweets from a user's timeline:

```bash
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dankoe",
    "limit": 20
  }'
```

**Response**:
```json
{
  "status": "success",
  "platform": "twitter",
  "target": "dankoe",
  "count": 20,
  "content_ids": ["uuid1", "uuid2", "..."]
}
```

---

### 3. Scrape YouTube Video

Extract transcript and metadata from a YouTube video:

```bash
curl -X POST http://localhost:8000/scrape/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "target": "dQw4w9WgXcQ",
    "limit": 1
  }'
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

---

### 4. Scrape Reddit Posts

Scrape top posts from a subreddit:

```bash
curl -X POST http://localhost:8000/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "target": "productivity",
    "limit": 50
  }'
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

---

### 5. RAG Semantic Search

Query scraped content with natural language:

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

**Response**:
```json
{
  "query": "What does Dan Koe say about focus systems?",
  "results": [
    {
      "content_id": "550e8400-e29b-41d4-a716-446655440000",
      "distance": 0.234,
      "document": "Your focus determines your reality. Here's how to build...",
      "metadata": {
        "platform": "twitter",
        "author_id": "dankoe",
        "source_url": "https://twitter.com/dankoe/status/123",
        "likes": 1234
      }
    }
  ],
  "count": 10
}
```

---

### 6. Analyze Content with LLM

Extract frameworks, hooks, and themes from content:

```bash
curl -X POST http://localhost:8000/analyze/content \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your focus determines your reality. Most people fail because they try to do everything at once. Here is my 2-hour focus block system: 1. Deep work only 2. No distractions 3. Single task focus"
  }'
```

**Response**:
```json
{
  "frameworks": ["AIDA"],
  "hooks": [
    {
      "type": "curiosity",
      "text": "Your focus determines your reality"
    }
  ],
  "themes": ["focus", "productivity", "deep work"],
  "pain_points": ["trying to do everything at once", "distractions"],
  "key_insights": ["2-hour focus blocks", "Single task focus"],
  "sentiment": "positive",
  "tone": "authoritative"
}
```

---

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_api.py

# Run specific test
pytest tests/unit/test_scrapers.py::test_twitter_scraper
```

### Integration Tests

```bash
# Run integration tests (requires services running)
pytest tests/integration/

# Run with verbose output
pytest -v tests/integration/
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

---

## Project Structure

```
research/
├── README.md                   # This file - Quick start guide
├── CLAUDE.md                   # Comprehensive project context
├── ORCHESTRATION.md            # Team execution guide
├── CCW_START.md                # Claude Code Web onboarding
├── .env.example                # Environment variables template
├── pytest.ini                  # Pytest configuration
├── podman-compose.yml          # Container orchestration
│
├── docs/                       # Documentation
│   ├── API.md                  # API endpoint reference
│   ├── INTEGRATION.md          # Integration patterns
│   ├── pm/                     # Project management docs
│   ├── dev/                    # Development documentation
│   ├── research/               # Research artifacts
│   └── agents/                 # Agent task prompts
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Pytest fixtures
│
├── tools/                      # Utilities
│   ├── doc-scraper/            # Documentation scraper
│   └── yt-agent-app/           # YouTube agent tool
│
└── scripts/                    # Automation scripts
```

**Backend Code** (shared with other modules):
```
../backend/                     # Shared IAC-011 backend
├── main.py                     # FastAPI application
├── api/                        # API routes
│   └── routes/
│       ├── scrape.py           # Scraping endpoints
│       ├── query.py            # RAG query endpoints
│       ├── analyze.py          # Analysis endpoints
│       └── health.py           # Health checks
├── scrapers/                   # Platform adapters
│   ├── base.py                 # Base scraper class
│   └── adapters/
│       ├── twitter.py          # Twitter scraper
│       ├── youtube.py          # YouTube scraper
│       ├── reddit.py           # Reddit scraper
│       └── web.py              # Web scraper
├── db/                         # Database layer
│   ├── models.py               # SQLAlchemy models
│   └── connection.py           # Database connection
├── vector/                     # Vector store
│   ├── chromadb_client.py      # ChromaDB client
│   └── embeddings.py           # Embedding generation
├── analysis/                   # LLM analysis
│   ├── analyzer.py             # Content analyzer
│   └── prompts.py              # LLM prompts
└── queue/                      # Async jobs
    └── tasks.py                # Celery tasks
```

---

## Environment Variables Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `sk-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `CHROMA_PORT` | ChromaDB port | `8000` |
| `ANTHROPIC_API_KEY` | Claude API key | None |
| `SCRAPERAPI_KEY` | ScraperAPI key | None |
| `JINA_API_KEY` | Jina.ai API key | None |
| `REDDIT_CLIENT_ID` | Reddit OAuth client ID | None |
| `REDDIT_CLIENT_SECRET` | Reddit OAuth secret | None |

---

## Common Tasks

### Start Services (Podman Compose)

```bash
# Start all services
podman-compose up -d

# View logs
podman-compose logs -f research

# Stop services
podman-compose down

# Restart single service
podman-compose restart research
```

### Database Operations

```bash
# Connect to PostgreSQL
psql -U scraper -d unified_scraper

# View contents table
SELECT platform, COUNT(*) FROM contents GROUP BY platform;

# View recent scrapes
SELECT * FROM contents ORDER BY scraped_at DESC LIMIT 10;

# Clear all data (CAUTION!)
TRUNCATE contents, authors, patterns RESTART IDENTITY CASCADE;
```

### ChromaDB Operations

```bash
# Check ChromaDB health
curl http://localhost:8000/api/v1/heartbeat

# List collections
curl http://localhost:8000/api/v1/collections

# Get collection info
curl http://localhost:8000/api/v1/collections/unified_content
```

### Monitor Redis

```bash
# Connect to Redis CLI
redis-cli

# View all keys
KEYS *

# Monitor commands in real-time
MONITOR

# Check queue size
LLEN scraping_queue
```

---

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Make changes
# ... edit files ...

# Run tests
pytest

# Run linter
ruff check backend/
mypy backend/

# Commit changes
git add .
git commit -m "feat(research): Add new feature"
```

### 2. Adding a New Scraper

**Create adapter**:
```python
# backend/scrapers/adapters/newplatform.py
from backend.scrapers.base import BaseScraper

class NewPlatformScraper(BaseScraper):
    async def extract(self, target: str, limit: int):
        # Scraping logic
        pass

    async def normalize(self, raw_data: dict):
        # Convert to UnifiedContent
        pass

    async def health_check(self):
        return {"status": "ok", "platform": "newplatform"}
```

**Register adapter**:
```python
# backend/scrapers/registry.py
from backend.scrapers.adapters.newplatform import NewPlatformScraper

SCRAPER_REGISTRY = {
    "twitter": TwitterScraper,
    "youtube": YouTubeScraper,
    "reddit": RedditScraper,
    "newplatform": NewPlatformScraper,  # Add here
}
```

**Test scraper**:
```python
# tests/unit/test_scrapers.py
@pytest.mark.asyncio
async def test_newplatform_scraper():
    scraper = NewPlatformScraper()
    data = await scraper.extract("target", 10)
    assert len(data) == 10
```

### 3. Adding a New Endpoint

```python
# backend/api/routes/scrape.py
@router.post("/newplatform")
async def scrape_newplatform(request: ScrapeRequest):
    scraper = get_scraper("newplatform")
    data = await scraper.extract(request.target, request.limit)
    return {"status": "success", "count": len(data)}
```

---

## Deployment

### Local Development

```bash
# Start services
podman-compose up -d

# Run API server
uvicorn backend.main:app --reload --port 8000

# Access at http://localhost:8000
```

### Production (Hetzner VPS)

```bash
# SSH into server
ssh root@your-server-ip

# Clone repository
git clone https://github.com/Iamcodio/IAC-033-extrophi-ecosystem.git
cd IAC-033-extrophi-ecosystem/research

# Set environment variables
cp .env.example .env
nano .env  # Edit with production values

# Start with Podman Compose
podman-compose up -d

# Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/research

# Enable site
sudo ln -s /etc/nginx/sites-available/research /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### API Won't Start

**Error**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Make sure you're in the repository root
cd /path/to/extrophi-ecosystem

# Verify PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Activate virtual environment
source .venv/bin/activate
```

### Database Connection Failed

**Error**: `FATAL: database "unified_scraper" does not exist`

**Solution**:
```bash
# Create database
psql -U scraper -c "CREATE DATABASE unified_scraper;"

# Install pgvector extension
psql -U scraper -d unified_scraper -c "CREATE EXTENSION vector;"
```

### ChromaDB Connection Refused

**Error**: `ConnectionRefusedError: [Errno 111] Connection refused`

**Solution**:
```bash
# Check ChromaDB is running
podman ps | grep chromadb

# Restart ChromaDB
podman-compose restart chromadb

# Check ChromaDB logs
podman logs research_chromadb_1
```

### OpenAI API Key Invalid

**Error**: `openai.error.AuthenticationError: Invalid API key`

**Solution**:
```bash
# Verify API key in .env
cat .env | grep OPENAI_API_KEY

# Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Documentation

### Full Documentation

- **[API.md](docs/API.md)** - Complete API endpoint reference
- **[INTEGRATION.md](docs/INTEGRATION.md)** - Integration patterns with Writer/Backend
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive project context
- **[ORCHESTRATION.md](ORCHESTRATION.md)** - Team workflow guide

### Interactive API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Tech Stack

### Core

- **FastAPI** - Modern async Python web framework
- **PostgreSQL 16** - Primary database with pgvector extension
- **ChromaDB** - Vector database for semantic search
- **Redis** - Job queue and caching
- **OpenAI GPT-4** - LLM analysis and embeddings
- **Claude Sonnet 4.5** - Copywriting analysis

### Platform Libraries

- **Playwright** - Browser automation (Twitter OAuth)
- **youtube-transcript-api** - YouTube transcript extraction
- **PRAW** - Reddit API wrapper
- **ScraperAPI** - Robust web scraping (paid)
- **Jina.ai Reader** - Web content extraction (FREE)

### Development

- **UV** - Fast Python package manager
- **Pytest** - Testing framework
- **Ruff** - Python linter
- **MyPy** - Static type checker
- **Podman Compose** - Container orchestration

---

## Contributing

This project uses a **research → document → command** workflow:

1. **Research** - Investigate solutions and document findings
2. **Document** - Create architecture specs and decision logs
3. **Command** - Execute implementation via GitHub Issues

See **[ORCHESTRATION.md](ORCHESTRATION.md)** for contribution guidelines.

---

## Support

### GitHub Issues

Report bugs and request features: https://github.com/Iamcodio/IAC-033-extrophi-ecosystem/issues

### Documentation Issues

If you find errors in documentation, please open an issue with:
- Page URL or file path
- Description of the error
- Suggested correction

---

## License

Private project - All rights reserved

---

## Contact

**GitHub**: [@iamcodio](https://github.com/Iamcodio)
**Project**: IAC-032 Unified Scraper
**Part of**: IAC-033 Extrophi Ecosystem
**Status**: Active Development

---

**Last Updated**: 2025-11-18
**Quick Start Guide**: Agent NU #40

---

*Built with Claude Code - The blacksmith's forge for content empires.*
