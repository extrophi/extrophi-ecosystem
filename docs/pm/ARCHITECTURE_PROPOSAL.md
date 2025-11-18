# Architecture Proposal - Unified Scraper Engine

**For**: Product Development Manager Review
**Date**: 2025-11-16
**Project**: IAC-032 Unified Scraper
**Status**: PROPOSAL - Awaiting Approval

---

## Executive Summary

Build a containerized, modular content intelligence engine that:
1. Runs on Hetzner VPS (production)
2. Uses ScraperAPI for proxy/IP rotation
3. Deploys independent scraper modules (Twitter, YouTube, Reddit, Web)
4. Automated CI/CD pipeline (GitHub Actions → Hetzner)
5. Each module developed by independent CCW team

**Total MVP Time**: 6-7 hours parallel execution
**Deployment**: Push to Hetzner in <1 hour after MVP complete
**Cost**: $20-89/mo operational (vs competitors $49-299/mo)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     HETZNER VPS INSTANCE                    │
│                    (Production Environment)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   PODMAN    │    │   PODMAN    │    │   PODMAN    │    │
│  │  PostgreSQL │    │    Redis    │    │  ChromaDB   │    │
│  │  + pgvector │    │   (Queue)   │    │    (RAG)    │    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│  ┌─────────────────────────┴─────────────────────────┐     │
│  │              CORE ENGINE (FastAPI)                 │     │
│  │                                                    │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │     │
│  │  │ /scrape  │  │ /query   │  │/generate │       │     │
│  │  │ endpoint │  │   /rag   │  │  /course │       │     │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘       │     │
│  │       │              │              │             │     │
│  │       ▼              ▼              ▼             │     │
│  │  ┌─────────────────────────────────────────┐     │     │
│  │  │         SCRAPER FACTORY                  │     │     │
│  │  │    (Routes to appropriate module)        │     │     │
│  │  └─────────────────────────────────────────┘     │     │
│  └─────────────────────────────────────────────────┘     │
│                            │                                │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼            │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │   TWITTER   │   │   YOUTUBE   │   │   REDDIT    │      │
│  │   MODULE    │   │   MODULE    │   │   MODULE    │      │
│  │  (Podman)   │   │  (Podman)   │   │  (Podman)   │      │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘      │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘            │
│                            │                                │
│                            ▼                                │
│                  ┌─────────────────┐                       │
│                  │   SCRAPER API   │                       │
│                  │  (Proxy Layer)  │                       │
│                  │  IP Rotation    │                       │
│                  │  Anti-Detection │                       │
│                  └────────┬────────┘                       │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   INTERNET    │
                    │  Twitter.com  │
                    │  YouTube.com  │
                    │  Reddit.com   │
                    │  Amazon.com   │
                    └───────────────┘
```

---

## Container Stack (Podman)

### Core Infrastructure Containers

**1. PostgreSQL + pgvector**
```yaml
# podman-compose.yml
postgres:
  image: pgvector/pgvector:pg16
  container_name: unified_scraper_db
  ports:
    - "5432:5432"
  environment:
    POSTGRES_DB: unified_scraper
    POSTGRES_USER: scraper
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - ./data/postgres:/var/lib/postgresql/data
  restart: always
```

**2. Redis (Job Queue)**
```yaml
redis:
  image: redis:7-alpine
  container_name: unified_scraper_queue
  ports:
    - "6379:6379"
  volumes:
    - ./data/redis:/data
  restart: always
```

**3. ChromaDB (RAG Vector Store)**
```yaml
chromadb:
  image: chromadb/chroma:latest
  container_name: unified_scraper_rag
  ports:
    - "8001:8000"
  volumes:
    - ./data/chromadb:/chroma/chroma
  restart: always
```

**4. Core Engine (FastAPI)**
```yaml
core_engine:
  build: ./backend
  container_name: unified_scraper_core
  ports:
    - "8000:8000"
  environment:
    DATABASE_URL: postgresql://scraper:${DB_PASSWORD}@postgres:5432/unified_scraper
    REDIS_URL: redis://redis:6379
    CHROMADB_URL: http://chromadb:8000
    SCRAPER_API_KEY: ${SCRAPER_API_KEY}
    OPENAI_API_KEY: ${OPENAI_API_KEY}
  depends_on:
    - postgres
    - redis
    - chromadb
  restart: always
```

### Scraper Module Containers (Independent)

**5. Twitter Scraper Module**
```yaml
twitter_scraper:
  build: ./scrapers/twitter
  container_name: unified_scraper_twitter
  environment:
    SCRAPER_API_KEY: ${SCRAPER_API_KEY}
    CORE_ENGINE_URL: http://core_engine:8000
  volumes:
    - ./data/twitter_profile:/app/data/profile
  restart: always
```

**6. YouTube Scraper Module**
```yaml
youtube_scraper:
  build: ./scrapers/youtube
  container_name: unified_scraper_youtube
  environment:
    SCRAPER_API_KEY: ${SCRAPER_API_KEY}
    CORE_ENGINE_URL: http://core_engine:8000
    OPENAI_API_KEY: ${OPENAI_API_KEY}  # For Whisper
  restart: always
```

**7. Reddit Scraper Module**
```yaml
reddit_scraper:
  build: ./scrapers/reddit
  container_name: unified_scraper_reddit
  environment:
    REDDIT_CLIENT_ID: ${REDDIT_CLIENT_ID}
    REDDIT_CLIENT_SECRET: ${REDDIT_CLIENT_SECRET}
    CORE_ENGINE_URL: http://core_engine:8000
  restart: always
```

**8. Web Scraper Module (ScraperAPI Direct)**
```yaml
web_scraper:
  build: ./scrapers/web
  container_name: unified_scraper_web
  environment:
    SCRAPER_API_KEY: ${SCRAPER_API_KEY}
    JINA_API_KEY: ${JINA_API_KEY}  # FREE tier
    CORE_ENGINE_URL: http://core_engine:8000
  restart: always
```

---

## ScraperAPI Integration

### What ScraperAPI Provides

**Proxy Infrastructure** (we don't build this):
- Automatic IP rotation (millions of IPs)
- Residential proxies (appear as real users)
- Geographic targeting (US, EU, etc.)
- Anti-bot bypass (CAPTCHA solving)
- JavaScript rendering (headless Chrome)

**Cost**: $49/mo for 100K API credits
- Simple request: 1 credit
- JS rendering: 5 credits
- Structured data (Amazon, Google): 5-25 credits

### API Endpoints We Use

**1. General Web Scraping**
```python
# Any website with proxy rotation
import requests

def scrape_with_proxy(url: str, render_js: bool = False) -> str:
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": str(render_js).lower()
    }
    response = requests.get("https://api.scraperapi.com", params=params)
    return response.text  # HTML content
```

**2. Amazon Structured Data**
```python
# Clean JSON product/review data
def scrape_amazon_reviews(product_url: str) -> dict:
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": product_url,
        "amazon_domain": "com",
        "type": "reviews"
    }
    response = requests.get(
        "https://api.scraperapi.com/structured/amazon/reviews",
        params=params
    )
    return response.json()  # Structured review data
```

**3. Google SERP Data**
```python
# Search engine results for competitive analysis
def scrape_google_serp(query: str) -> dict:
    params = {
        "api_key": SCRAPER_API_KEY,
        "query": query,
        "country_code": "us"
    }
    response = requests.get(
        "https://api.scraperapi.com/structured/google/search",
        params=params
    )
    return response.json()  # Search results with rankings
```

### When to Use ScraperAPI vs Direct APIs

| Platform | Method | Why |
|----------|--------|-----|
| Twitter | IAC-024 Playwright (direct) | Anti-detection already built, saves credits |
| YouTube | youtube-transcript-api (direct) | Official API, no cost |
| Reddit | PRAW (direct) | Official API, 1,000 req/10min FREE |
| Amazon | ScraperAPI structured | No official API, anti-bot required |
| Web/Blogs | Jina.ai FREE first | 50K pages/month free, fallback to ScraperAPI |
| Google SERP | ScraperAPI or DataForSEO | Competitive analysis |

**Strategy**: Use FREE/direct APIs first, ScraperAPI as fallback for complex sites.

---

## Module Independence (CCW Team per Module)

### Why Modular?

Each scraper module is:
- **Independent codebase** (own Dockerfile, own tests)
- **Separate CCW team** (no conflicts)
- **Hot-swappable** (update one without breaking others)
- **Scalable** (add new platforms in 30 min)

### Module Interface (Contract)

Every scraper module implements:

```python
# scrapers/{platform}/main.py

from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def health_check(self) -> dict:
        """Return module health status."""
        pass

    @abstractmethod
    def extract(self, target: str, limit: int = 20) -> list[dict]:
        """Extract raw data from platform."""
        pass

    @abstractmethod
    def normalize(self, raw_data: dict) -> dict:
        """Convert to unified schema."""
        pass

# HTTP API for inter-container communication
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return scraper.health_check()

@app.post("/extract")
def extract(request: ExtractRequest):
    return scraper.extract(request.target, request.limit)

@app.post("/normalize")
def normalize(request: NormalizeRequest):
    return scraper.normalize(request.raw_data)
```

### Core Engine Routes to Modules

```python
# backend/services/scraper_factory.py

SCRAPER_MODULES = {
    "twitter": "http://twitter_scraper:8000",
    "youtube": "http://youtube_scraper:8000",
    "reddit": "http://reddit_scraper:8000",
    "web": "http://web_scraper:8000"
}

async def scrape(platform: str, target: str, limit: int = 20):
    module_url = SCRAPER_MODULES[platform]

    # Call module's extract endpoint
    response = await httpx.post(
        f"{module_url}/extract",
        json={"target": target, "limit": limit}
    )
    raw_data = response.json()

    # Normalize to unified schema
    normalized = await httpx.post(
        f"{module_url}/normalize",
        json={"raw_data": raw_data}
    )

    return normalized.json()
```

---

## CI/CD Pipeline (GitHub Actions)

### Workflow: Code → Test → Deploy

```
Developer (CCW) pushes code
        │
        ▼
┌─────────────────┐
│  GitHub Actions │
│    Triggered    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────┐
│   Lint & Type   │────▶│    FAIL     │
│     Check       │     │  Back to    │
│   (ruff, mypy)  │     │    CCW      │
└────────┬────────┘     └─────────────┘
         │ PASS
         ▼
┌─────────────────┐     ┌─────────────┐
│   Unit Tests    │────▶│    FAIL     │
│    (pytest)     │     │  Back to    │
│                 │     │    CCW      │
└────────┬────────┘     └─────────────┘
         │ PASS
         ▼
┌─────────────────┐     ┌─────────────┐
│  Build Podman   │────▶│    FAIL     │
│    Containers   │     │  Back to    │
│                 │     │    CCW      │
└────────┬────────┘     └─────────────┘
         │ PASS
         ▼
┌─────────────────┐     ┌─────────────┐
│  Integration    │────▶│    FAIL     │
│     Tests       │     │  Back to    │
│                 │     │    CCW      │
└────────┬────────┘     └─────────────┘
         │ PASS
         ▼
┌─────────────────┐
│  Deploy to      │
│   Hetzner       │
│  (SSH + Podman) │
└─────────────────┘
```

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy --ignore-missing-imports .

  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio
      - run: pytest tests/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build containers
        run: |
          podman build -t unified_scraper_core ./backend
          podman build -t unified_scraper_twitter ./scrapers/twitter
          podman build -t unified_scraper_youtube ./scrapers/youtube
          podman build -t unified_scraper_reddit ./scrapers/reddit

  integration:
    needs: build
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration/ -v

  deploy:
    needs: integration
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Hetzner
        env:
          HETZNER_SSH_KEY: ${{ secrets.HETZNER_SSH_KEY }}
          HETZNER_HOST: ${{ secrets.HETZNER_HOST }}
        run: |
          # SSH into Hetzner and pull latest
          ssh -i $HETZNER_SSH_KEY root@$HETZNER_HOST << 'EOF'
            cd /opt/unified_scraper
            git pull origin main
            podman-compose down
            podman-compose up -d --build
          EOF
```

### Test Requirements (What Must Pass)

**Unit Tests** (each module):
```python
# tests/test_twitter_scraper.py
def test_normalize_tweet():
    raw = {"id": "123", "text": "Focus", "likes": 100}
    result = TwitterScraper().normalize(raw)
    assert result["platform"] == "twitter"
    assert result["body"] == "Focus"
    assert result["metrics"]["likes"] == 100

# tests/test_youtube_scraper.py
def test_extract_transcript():
    scraper = YouTubeScraper()
    result = scraper.extract("dQw4w9WgXcQ")
    assert "transcript" in result
    assert len(result["transcript"]) > 100
```

**Integration Tests** (end-to-end):
```python
# tests/integration/test_scrape_endpoint.py
def test_scrape_twitter():
    response = client.post("/scrape", json={
        "platform": "twitter",
        "target": "dankoe",
        "limit": 5
    })
    assert response.status_code == 200
    assert "job_id" in response.json()
```

**Build Must Succeed**:
- All Dockerfiles build without errors
- No missing dependencies
- Containers start and respond to health checks

---

## Hetzner Deployment

### Server Requirements

**Recommended**: CX31 (€12/mo)
- 4 vCPU
- 8 GB RAM
- 80 GB SSD
- Ubuntu 22.04

**Why this spec**:
- PostgreSQL + pgvector: 2 GB RAM
- Redis: 256 MB RAM
- ChromaDB: 1 GB RAM
- Core Engine: 512 MB RAM
- Scraper modules: 500 MB each
- Buffer for spikes: 2 GB

### Initial Setup (One-Time)

```bash
# On Hetzner VPS

# Install Podman
apt update && apt install -y podman podman-compose

# Clone repository
git clone https://github.com/Iamcodio/IAC-032-unified-scraper.git /opt/unified_scraper
cd /opt/unified_scraper

# Create .env file
cat > .env << EOF
DB_PASSWORD=your_secure_password
SCRAPER_API_KEY=your_key
OPENAI_API_KEY=your_key
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
EOF

# Start all containers
podman-compose up -d

# Verify
podman ps  # Should show 7+ containers running
curl http://localhost:8000/health  # Should return OK
```

### Deployment Flow

1. **Local development** (your machine or CCW)
2. **Push to GitHub** (triggers CI/CD)
3. **Tests pass** (lint, unit, build, integration)
4. **Auto-deploy** (GitHub Actions SSH into Hetzner)
5. **Hetzner pulls latest** and rebuilds containers
6. **Zero-downtime** (podman-compose handles gracefully)

---

## CCW Team Assignments (Independent Modules)

### Team Structure

**Team 1: Core Infrastructure** (FIRST - blocks others)
- PostgreSQL + pgvector container
- Redis queue container
- ChromaDB container
- podman-compose.yml setup
- **Duration**: 2-3 hours

**Team 2: Core Engine**
- FastAPI application
- Scraper factory (routing)
- Database connection
- Redis job queue integration
- **Duration**: 3-4 hours

**Team 3: Twitter Scraper Module**
- Port IAC-024 code
- Wrap in module interface
- Dockerfile
- Tests
- **Duration**: 3-4 hours

**Team 4: YouTube Scraper Module**
- youtube-transcript-api + Whisper fallback
- Module interface
- Dockerfile
- Tests
- **Duration**: 2-3 hours

**Team 5: Reddit Scraper Module**
- PRAW integration
- Module interface
- Dockerfile
- Tests
- **Duration**: 1-2 hours

**Team 6: Web Scraper Module**
- Jina.ai (FREE) + ScraperAPI fallback
- Module interface
- Dockerfile
- Tests
- **Duration**: 2-3 hours

**Team 7: CI/CD Pipeline**
- GitHub Actions workflow
- Test configuration
- Hetzner deployment script
- **Duration**: 2-3 hours

**All teams work in parallel after Team 1 completes.**

---

## Repository Structure

```
IAC-032-unified-scraper/
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions pipeline
├── backend/                       # Core Engine
│   ├── Dockerfile
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   ├── db/
│   │   ├── connection.py
│   │   └── models.py
│   └── services/
│       ├── scraper_factory.py
│       └── queue.py
├── scrapers/                      # Independent Modules
│   ├── twitter/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── tests/
│   ├── youtube/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── tests/
│   ├── reddit/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── tests/
│   └── web/
│       ├── Dockerfile
│       ├── main.py
│       └── tests/
├── tests/                         # Integration tests
│   ├── unit/
│   └── integration/
├── data/                          # Persistent volumes
│   ├── postgres/
│   ├── redis/
│   └── chromadb/
├── podman-compose.yml             # Container orchestration
├── .env.example                   # Environment template
└── docs/
    └── pm/
        └── ARCHITECTURE_PROPOSAL.md  # This document
```

---

## Risk Assessment

### Technical Risks

**Risk 1**: Container networking issues
- **Mitigation**: Use Podman pod (shared network namespace)
- **Fallback**: Host networking mode

**Risk 2**: ScraperAPI rate limits
- **Mitigation**: Redis queue with backoff
- **Fallback**: Direct scraping for supported platforms

**Risk 3**: Module communication failure
- **Mitigation**: Health checks + retry logic
- **Fallback**: Core engine includes fallback scrapers

**Risk 4**: Hetzner deployment fails
- **Mitigation**: CI/CD validates before deploy
- **Fallback**: Manual deployment via SSH

### Operational Risks

**Risk 5**: ScraperAPI credits exhausted
- **Mitigation**: Use FREE tier (Jina.ai) first
- **Monitor**: Track usage in dashboard

**Risk 6**: Database corruption
- **Mitigation**: Daily backups to object storage
- **Recovery**: Restore from backup in <1 hour

---

## Cost Analysis

### Infrastructure

| Component | Cost/Month |
|-----------|------------|
| Hetzner VPS (CX31) | €12 |
| ScraperAPI (Hobby) | $49 |
| OpenAI (embeddings + analysis) | $20 |
| **Total** | **$69 + €12 = ~$83/mo** |

### Comparison to Competitors

| Service | Cost/Month | Platforms | Pattern Detection |
|---------|------------|-----------|-------------------|
| **Us** | $83 | Multi (Twitter, YouTube, Reddit, Web) | ✅ Yes |
| TweetHunter | $49-99 | Twitter only | ❌ No |
| SuperX | $29 | Twitter only | ❌ No |

**ROI**: We're 1.7x cheaper than TweetHunter with 4x more platforms + pattern detection.

---

## Timeline

### Week 1 (Day 1-3): MVP

**Day 1** (COMPLETE):
- ✅ Research (20,946 lines documentation)
- ✅ Architecture design
- ✅ CI/CD pipeline setup
- ✅ Team assignments

**Day 2** (6-7 hours):
- Team 1: Core infrastructure (Podman containers)
- Teams 2-6: All modules in parallel
- Team 7: CI/CD pipeline

**Day 3** (4-6 hours):
- Integration testing
- Pattern detection
- Hetzner deployment
- End-to-end validation

### Week 2: Polish

- Tauri desktop frontend
- Advanced ranking algorithms
- Content gap analysis
- Course script generator

---

## Success Criteria (MVP)

### Must Pass (Day 3)

- [ ] All containers run on Hetzner (`podman ps` shows 7+ containers)
- [ ] POST /scrape works for Twitter, YouTube, Reddit
- [ ] Data stored in PostgreSQL with vector embeddings
- [ ] Semantic search returns results in <2 seconds
- [ ] GitHub Actions pipeline green (all tests pass)
- [ ] Zero manual intervention after git push

### Quality Gates

- [ ] Lint passes (ruff)
- [ ] Type checks pass (mypy)
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Containers build successfully
- [ ] Health checks respond 200 OK

---

## Approval Request

**Requesting approval to proceed with**:

1. **Containerized architecture** (Podman, not bare metal)
2. **Modular scraper design** (independent CCW teams per module)
3. **ScraperAPI integration** (proxy layer, not DIY)
4. **GitHub Actions CI/CD** (automated testing and deployment)
5. **Hetzner VPS** (production environment)

**Your Role**: QA/QC, workflow setup, research, documentation
**CCW Teams Role**: All coding (unlimited resources, automated retry on failure)
**Pipeline**: Code fails test → back to CCW, passes → auto-deploy

---

**Awaiting your review and approval to spawn CCW teams.**
