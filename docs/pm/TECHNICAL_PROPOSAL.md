# TECHNICAL PROPOSAL - IAC-032 Unified Scraper

**Project**: Multi-Platform Content Intelligence Engine
**Version**: 1.0.0
**Status**: PROPOSAL - Awaiting PM Approval
**Author**: Claude Code Architecture Team
**Date**: 2025-11-16
**Review Required By**: Product Development Manager

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [System Architecture Diagrams](#3-system-architecture-diagrams)
4. [Technology Stack Decision Matrix](#4-technology-stack-decision-matrix)
5. [Agent Team Structure](#5-agent-team-structure)
6. [Risk Assessment](#6-risk-assessment)
7. [Cost Analysis](#7-cost-analysis)
8. [Implementation Timeline](#8-implementation-timeline)
9. [Deployment Strategy](#9-deployment-strategy)
10. [CI/CD Pipeline](#10-cicd-pipeline)
11. [Success Criteria](#11-success-criteria)
12. [Appendix A: API Specifications](#appendix-a-api-specifications)
13. [Appendix B: Database Schema](#appendix-b-database-schema)
14. [Appendix C: Environment Variables](#appendix-c-environment-variables)

---

## 1. Executive Summary

### Project Overview

IAC-032 Unified Scraper is a containerized, multi-platform content intelligence engine designed to scrape, analyze, and synthesize content from Twitter, YouTube, Reddit, Amazon, and web sources. The system uses 7 parallel Claude Code Web (CCW) agents to deliver a production-ready MVP in 6-7 hours of parallel execution time.

### Core Value Proposition

**Problem**: Content creators spend 10+ hours/week manually researching competitors across multiple platforms, losing insights buried in fragmented data.

**Solution**: Automated multi-platform scraping with RAG-powered semantic search, LLM-driven pattern detection, and production-ready content brief generation.

**Competitive Advantage**:
- **Multi-platform** vs single-platform (TweetHunter, SuperX)
- **Pattern detection** via cross-platform elaboration analysis
- **70% cheaper** than competitors ($20-89/mo vs $49-299/mo)
- **Course script generation** from raw research (unique feature)

### Technical Approach

**Container Stack** (Podman on Hetzner VPS):
- PostgreSQL 16 + pgvector (vector similarity search)
- Redis 7 + RQ (job queue orchestration)
- ChromaDB (RAG semantic search)
- FastAPI (Python backend services)
- 4 independent scraper modules (Twitter, YouTube, Reddit, Web)

**Key Metrics**:
- **MVP Time**: 6-7 hours (parallel execution)
- **Deployment**: <1 hour to Hetzner production
- **Monthly Cost**: $20-89 (FREE tier first, paid fallback)
- **Test Coverage**: >80% unit tests, full integration suite
- **Response Time**: Semantic search <2 seconds

### Agent Team Summary

| Agent | Codename | Mission | Hours | Critical Path |
|-------|----------|---------|-------|---------------|
| Alpha | Database Architect | PostgreSQL + pgvector setup | 1-2h | BLOCKS ALL |
| Beta | Twitter Specialist | Port IAC-024 anti-detection | 3-4h | Parallel |
| Gamma | API Engineer | FastAPI backend services | 2-3h | Parallel |
| Delta | YouTube Specialist | Transcripts + Whisper fallback | 2-3h | Parallel |
| Epsilon | Reddit Specialist | PRAW official API | 1-2h | Parallel |
| Zeta | RAG Engineer | ChromaDB + OpenAI embeddings | 2-3h | Parallel |
| Eta | DevOps Engineer | CI/CD + Hetzner deployment | 2-3h | Parallel |

---

## 2. Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        HETZNER VPS INSTANCE                     │
│                      (CX31: 4 vCPU, 8GB RAM)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │   ChromaDB   │          │
│  │  + pgvector  │  │   (Queue)    │  │    (RAG)     │          │
│  │   Port 5432  │  │  Port 6379   │  │  Port 8001   │          │
│  └───────┬──────┘  └───────┬──────┘  └───────┬──────┘          │
│          │                 │                 │                  │
│          └─────────────────┼─────────────────┘                  │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────┐          │
│  │              CORE ENGINE (FastAPI)                 │          │
│  │                    Port 8000                       │          │
│  │                                                    │          │
│  │   /scrape    /query/rag    /analyze    /generate  │          │
│  │                                                    │          │
│  │   ┌─────────────────────────────────────────┐     │          │
│  │   │           SCRAPER FACTORY               │     │          │
│  │   │     (Routes to platform modules)        │     │          │
│  │   └─────────────────────────────────────────┘     │          │
│  └─────────────────────────────────────────────────┘            │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   TWITTER   │   │   YOUTUBE   │   │   REDDIT    │           │
│  │   MODULE    │   │   MODULE    │   │   MODULE    │           │
│  │  Port 8010  │   │  Port 8020  │   │  Port 8030  │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                  │                  │                  │
│         │          ┌───────┴──────┐          │                  │
│         │          │  WEB MODULE  │          │                  │
│         │          │  Port 8040   │          │                  │
│         │          └───────┬──────┘          │                  │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                 │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    INTERNET     │
                    │  Twitter.com    │
                    │  YouTube.com    │
                    │  Reddit.com     │
                    │  Jina.ai (FREE) │
                    │  ScraperAPI     │
                    └─────────────────┘
```

### Design Principles

1. **Containerized Isolation**: Each component runs in its own Podman container
2. **Modular Adapters**: 30-minute platform addition cycle
3. **Contract-Based Communication**: All modules implement BaseScraper interface
4. **FREE Tier First**: Jina.ai (50K/mo), PRAW (1K/10min), youtube-transcript-api
5. **Paid Fallback**: ScraperAPI only for complex anti-bot sites
6. **Fail-Fast Pipeline**: CI/CD gates prevent broken code from deployment

---

## 3. System Architecture Diagrams

### 3.1 Container Stack Architecture

```mermaid
graph TB
    subgraph "Hetzner VPS (CX31)"
        subgraph "Infrastructure Layer"
            PG[("PostgreSQL 16<br/>+ pgvector<br/>Port 5432")]
            RD[("Redis 7 Alpine<br/>Port 6379")]
            CH[("ChromaDB<br/>Port 8001")]
        end

        subgraph "Application Layer"
            CE["FastAPI Core Engine<br/>Port 8000"]
        end

        subgraph "Scraper Modules"
            TW["Twitter Module<br/>Port 8010"]
            YT["YouTube Module<br/>Port 8020"]
            RE["Reddit Module<br/>Port 8030"]
            WB["Web Module<br/>Port 8040"]
        end
    end

    subgraph "External Services"
        SA["ScraperAPI<br/>($49/mo fallback)"]
        JN["Jina.ai Reader<br/>(50K FREE/mo)"]
        OA["OpenAI API<br/>(text-embedding-3-small)"]
        PW["PRAW<br/>(1K req/10min FREE)"]
        YTA["youtube-transcript-api<br/>(FREE)"]
    end

    CE --> PG
    CE --> RD
    CE --> CH
    CE --> TW
    CE --> YT
    CE --> RE
    CE --> WB

    TW --> SA
    YT --> YTA
    YT -.-> OA
    RE --> PW
    WB --> JN
    WB -.-> SA
    CE --> OA

    style PG fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    style RD fill:#DC382D,stroke:#333,stroke-width:2px,color:#fff
    style CH fill:#00875A,stroke:#333,stroke-width:2px,color:#fff
    style CE fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style TW fill:#1DA1F2,stroke:#333,stroke-width:2px,color:#fff
    style YT fill:#FF0000,stroke:#333,stroke-width:2px,color:#fff
    style RE fill:#FF4500,stroke:#333,stroke-width:2px,color:#fff
    style WB fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
```

### 3.2 Data Flow Pipeline

```mermaid
graph LR
    subgraph "Input Phase"
        A["Project Brief<br/>'Focus systems for creators'"]
        B["Target Authors<br/>@dankoe, Cal Newport"]
        C["Platform Config<br/>Twitter, YouTube, Reddit"]
    end

    subgraph "Scraping Phase"
        D["Queue Jobs<br/>(Redis + RQ)"]
        E["Platform Adapters<br/>(Module Containers)"]
        F["Rate Limiter<br/>(Exponential Backoff)"]
    end

    subgraph "Storage Phase"
        G["Raw Content<br/>(PostgreSQL)"]
        H["Vector Embeddings<br/>(ChromaDB)"]
        I["Metadata Index<br/>(pgvector)"]
    end

    subgraph "Analysis Phase"
        J["LLM Processing<br/>(GPT-4 bulk)"]
        K["Pattern Detection<br/>(Cross-platform)"]
        L["Framework Extraction<br/>(AIDA, PAS, BAB)"]
    end

    subgraph "Output Phase"
        M["Course Scripts<br/>(Production-ready)"]
        N["Content Briefs<br/>(Markdown)"]
        O["Tweet Threads<br/>(Formatted)"]
        P["Semantic Search<br/>(RAG queries)"]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    G --> I
    H --> J
    I --> J
    J --> K
    J --> L
    K --> M
    L --> N
    K --> O
    H --> P

    style A fill:#E3F2FD,stroke:#1976D2
    style M fill:#E8F5E9,stroke:#388E3C
    style N fill:#E8F5E9,stroke:#388E3C
    style O fill:#E8F5E9,stroke:#388E3C
    style P fill:#E8F5E9,stroke:#388E3C
```

### 3.3 CI/CD Pipeline Architecture

```mermaid
graph TD
    subgraph "Developer Workflow"
        DEV["CCW Agent<br/>Writes Code"]
        PR["Pull Request<br/>Created"]
    end

    subgraph "Gate 1: Code Quality"
        LINT["Ruff Linter<br/>(Python Style)"]
        TYPE["MyPy Type Check<br/>(Static Analysis)"]
    end

    subgraph "Gate 2: Unit Tests"
        PYTEST["Pytest<br/>(80% Coverage)"]
        MOCK["Mocked Dependencies<br/>(No External Calls)"]
    end

    subgraph "Gate 3: Build Verification"
        BUILD["Podman Build<br/>(All Containers)"]
        HEALTH["Health Checks<br/>(200 OK Response)"]
    end

    subgraph "Gate 4: Integration Tests"
        INT["End-to-End Tests<br/>(Real Database)"]
        API["API Contract Tests<br/>(OpenAPI Validation)"]
    end

    subgraph "Gate 5: Security Scan"
        SEC["Trivy Scanner<br/>(Container CVEs)"]
        CRED["Credential Detection<br/>(GitLeaks)"]
    end

    subgraph "Deployment"
        SSH["SSH to Hetzner<br/>(Automated)"]
        PULL["Git Pull<br/>(Latest Main)"]
        RESTART["Podman Compose<br/>(Zero Downtime)"]
    end

    DEV --> PR
    PR --> LINT
    LINT -->|PASS| TYPE
    TYPE -->|PASS| PYTEST
    LINT -->|FAIL| DEV
    TYPE -->|FAIL| DEV
    PYTEST --> MOCK
    MOCK -->|PASS| BUILD
    PYTEST -->|FAIL| DEV
    BUILD --> HEALTH
    HEALTH -->|PASS| INT
    BUILD -->|FAIL| DEV
    INT --> API
    API -->|PASS| SEC
    INT -->|FAIL| DEV
    SEC --> CRED
    CRED -->|PASS| SSH
    SEC -->|FAIL| DEV
    SSH --> PULL
    PULL --> RESTART

    style LINT fill:#FFF3E0,stroke:#FF9800
    style TYPE fill:#FFF3E0,stroke:#FF9800
    style PYTEST fill:#E3F2FD,stroke:#1976D2
    style BUILD fill:#F3E5F5,stroke:#9C27B0
    style INT fill:#E8F5E9,stroke:#388E3C
    style SEC fill:#FFEBEE,stroke:#D32F2F
    style RESTART fill:#C8E6C9,stroke:#2E7D32,stroke-width:3px
```

### 3.4 Agent Dependency Graph

```mermaid
graph TD
    subgraph "Phase 1: Foundation (Sequential)"
        ALPHA["ALPHA<br/>Database Architect<br/>1-2 hours<br/><b>CRITICAL BLOCKER</b>"]
    end

    subgraph "Phase 2: Parallel Execution (Simultaneous)"
        BETA["BETA<br/>Twitter Specialist<br/>3-4 hours"]
        GAMMA["GAMMA<br/>API Engineer<br/>2-3 hours"]
        DELTA["DELTA<br/>YouTube Specialist<br/>2-3 hours"]
        EPSILON["EPSILON<br/>Reddit Specialist<br/>1-2 hours"]
        ZETA["ZETA<br/>RAG Engineer<br/>2-3 hours"]
        ETA["ETA<br/>DevOps Engineer<br/>2-3 hours"]
    end

    subgraph "Phase 3: Integration (After Parallel)"
        INTEGRATION["System Integration<br/>Cross-module testing<br/>1 hour"]
    end

    ALPHA --> BETA
    ALPHA --> GAMMA
    ALPHA --> DELTA
    ALPHA --> EPSILON
    ALPHA --> ZETA
    ALPHA --> ETA

    BETA --> INTEGRATION
    GAMMA --> INTEGRATION
    DELTA --> INTEGRATION
    EPSILON --> INTEGRATION
    ZETA --> INTEGRATION
    ETA --> INTEGRATION

    style ALPHA fill:#D32F2F,stroke:#B71C1C,stroke-width:3px,color:#fff
    style BETA fill:#1976D2,stroke:#0D47A1,stroke-width:2px,color:#fff
    style GAMMA fill:#388E3C,stroke:#1B5E20,stroke-width:2px,color:#fff
    style DELTA fill:#FBC02D,stroke:#F9A825,stroke-width:2px
    style EPSILON fill:#7B1FA2,stroke:#4A148C,stroke-width:2px,color:#fff
    style ZETA fill:#F57C00,stroke:#E65100,stroke-width:2px
    style ETA fill:#00838F,stroke:#006064,stroke-width:2px,color:#fff
    style INTEGRATION fill:#C8E6C9,stroke:#2E7D32,stroke-width:3px
```

### 3.5 Scraper Factory Pattern

```mermaid
classDiagram
    class BaseScraper {
        <<abstract>>
        +config: dict
        +health_check() dict
        +extract(target: str, limit: int) list[dict]
        +normalize(raw_data: dict) UnifiedContent
    }

    class TwitterScraper {
        -session: PersistentXSession
        -oauth_client: PlaywrightOAuthClient
        +health_check() dict
        +extract(target: str, limit: int) list[dict]
        +normalize(raw_data: dict) UnifiedContent
        -_spoof_fingerprint() void
        -_simulate_human_behavior() void
    }

    class YouTubeScraper {
        -transcript_api: YouTubeTranscriptApi
        -whisper_model: whisper.Model
        +health_check() dict
        +extract(video_id: str, limit: int) list[dict]
        +normalize(raw_data: dict) UnifiedContent
        -_whisper_fallback(video_id: str) str
    }

    class RedditScraper {
        -reddit: praw.Reddit
        +health_check() dict
        +extract(subreddit: str, limit: int) list[dict]
        +normalize(raw_data: dict) UnifiedContent
        -_respect_rate_limit() void
    }

    class WebScraper {
        -jina_key: str
        -scraper_api_key: str
        +health_check() dict
        +extract(url: str, limit: int) list[dict]
        +normalize(raw_data: dict) UnifiedContent
        -_jina_fetch(url: str) str
        -_scraper_api_fallback(url: str) str
    }

    class ScraperFactory {
        -scrapers: dict[str, BaseScraper]
        +get_scraper(platform: str) BaseScraper
        +list_platforms() list[str]
    }

    class UnifiedContent {
        +content_id: UUID
        +platform: str
        +source_url: str
        +author_id: str
        +author_name: str
        +content_type: str
        +title: str
        +body: str
        +published_at: datetime
        +metrics: dict
        +analysis: dict
        +embedding: list[float]
        +scraped_at: datetime
        +metadata: dict
    }

    BaseScraper <|-- TwitterScraper
    BaseScraper <|-- YouTubeScraper
    BaseScraper <|-- RedditScraper
    BaseScraper <|-- WebScraper
    ScraperFactory --> BaseScraper : creates
    BaseScraper --> UnifiedContent : produces
```

---

## 4. Technology Stack Decision Matrix

### 4.1 Backend Framework

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **FastAPI** | **9/10** | Async native, auto-OpenAPI docs, Pydantic validation, <1h learning curve | Python GIL limitations | **SELECTED** |
| Flask | 6/10 | Simple, mature ecosystem | No async, manual validation | Rejected |
| Django | 5/10 | Batteries included | Overkill for API-only, slow startup | Rejected |
| Express.js | 7/10 | Fast, large ecosystem | JavaScript, no type safety | Rejected |

**Rationale**: FastAPI provides native async support critical for concurrent scraping, automatic OpenAPI documentation for testing, and Pydantic integration for type-safe data models. Learning curve is minimal for the 3-day sprint.

---

### 4.2 Database

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **PostgreSQL + pgvector** | **10/10** | ACID compliance, vector similarity, mature, battle-tested | Requires extension setup | **SELECTED** |
| SQLite + sqlite-vss | 6/10 | Zero setup, portable | No concurrent writes, limited scalability | Fallback Only |
| MongoDB | 5/10 | Schema flexibility | No vector native, consistency issues | Rejected |
| Pinecone | 7/10 | Managed vector DB | $70/mo cost, vendor lock-in | Rejected |

**Rationale**: PostgreSQL with pgvector provides native vector similarity search (<=> operator) combined with traditional relational queries. The ivfflat index enables <500ms similarity searches on 100K+ embeddings. Free, self-hosted, and battle-tested.

---

### 4.3 Vector Store / RAG

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **ChromaDB** | **9/10** | Local persistence, Python-native, free, HNSW algorithm | Memory hungry for large datasets | **SELECTED** |
| Pinecone | 7/10 | Managed, scalable | $70/mo minimum, vendor lock-in | Rejected |
| Weaviate | 7/10 | GraphQL API, hybrid search | Heavy (8GB RAM), complex setup | Rejected |
| FAISS | 6/10 | Fast, Facebook-proven | No persistence, index-only | Rejected |

**Rationale**: ChromaDB provides local persistence to `./data/chromadb`, Python-native API, and HNSW algorithm for fast approximate nearest neighbor search. Perfect for MVP scale (10K-100K documents). Free, no vendor lock-in.

---

### 4.4 Job Queue

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **Redis + RQ** | **9/10** | 15-minute learning curve, simple, Redis-only | Limited features vs Celery | **SELECTED** |
| Celery | 7/10 | Feature-rich, mature | 2-3 day learning curve, complex | Rejected (time constraint) |
| Dramatiq | 7/10 | Simple, reliable | Smaller ecosystem | Rejected |
| AWS SQS | 6/10 | Managed, scalable | Vendor lock-in, cost | Rejected |

**Rationale**: RQ (Redis Queue) has a 15-minute learning curve vs Celery's 2-3 day curve. For the 3-day sprint, simplicity trumps features. Redis provides persistence, and RQ handles retry logic with Tenacity integration.

---

### 4.5 Embedding Model

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **OpenAI text-embedding-3-small** | **10/10** | $0.00002/1K tokens, 1536 dims, high quality | External API dependency | **SELECTED** |
| OpenAI text-embedding-3-large | 8/10 | 3072 dims, higher accuracy | 5x cost, overkill for MVP | Rejected |
| Sentence Transformers (local) | 6/10 | Free, local | Lower quality, slow on CPU | Rejected |
| Cohere embed-v3 | 7/10 | Competitive pricing | Smaller ecosystem | Rejected |

**Rationale**: text-embedding-3-small provides the best cost/quality ratio at $0.00002/1K tokens. 1536 dimensions is sufficient for semantic similarity. Cost: $0.20 per 10K content items indexed.

---

### 4.6 LLM Analysis

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **GPT-4 (bulk processing)** | **9/10** | $0.0025/1K input, fast, reliable | Not best for copywriting | **SELECTED FOR BULK** |
| **Claude Sonnet 4.5 (polish)** | **10/10** | Best copywriting analysis, nuanced | $3/1M input (higher cost) | **SELECTED FOR FINAL** |
| GPT-3.5 Turbo | 7/10 | Cheapest | Lower quality analysis | Rejected |
| Local LLaMA | 5/10 | Free | Requires GPU, lower quality | Rejected |

**Rationale**: Hybrid approach - GPT-4 for bulk processing (framework extraction, hook identification) at low cost. Claude Sonnet 4.5 for final analysis and course script generation where copywriting quality matters.

---

### 4.7 Scraping Infrastructure

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **Jina.ai Reader (FREE tier)** | **10/10** | 50K pages/month FREE, markdown conversion | Static content only | **SELECTED (PRIMARY)** |
| **ScraperAPI ($49/mo)** | **8/10** | IP rotation, CAPTCHA solving, JS rendering | Cost per credit | **SELECTED (FALLBACK)** |
| Bright Data | 7/10 | Enterprise features | $500/mo minimum | Rejected (budget) |
| Apify | 7/10 | Actor marketplace | $49/mo for less features | Rejected |
| DIY Proxies | 4/10 | Full control | Maintenance nightmare | Rejected |

**Rationale**: FREE first, paid fallback. Jina.ai provides 50K pages/month at $0 cost. ScraperAPI ($49/mo) provides IP rotation and anti-bot bypass for complex sites only. Total scraping cost: $0-49/mo.

---

### 4.8 Container Orchestration

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **Podman** | **10/10** | Rootless, Docker-compatible, systemd integration | Smaller community | **SELECTED** |
| Docker | 9/10 | Industry standard, large ecosystem | Requires daemon, root by default | Rejected (security) |
| Kubernetes | 6/10 | Scalable, enterprise | Overkill for single VPS | Rejected |

**Rationale**: Podman is rootless by default (security), Docker-compose compatible, and has better systemd integration for Linux servers. Perfect for single-VPS deployment.

---

### 4.9 Deployment Target

| Technology | Score | Pros | Cons | Decision |
|------------|-------|------|------|----------|
| **Hetzner VPS (CX31)** | **10/10** | 12/mo, 4 vCPU, 8GB RAM, EU data center | Not US-based | **SELECTED** |
| DigitalOcean | 7/10 | Easy setup, popular | $48/mo for same specs | Rejected (cost) |
| AWS EC2 | 6/10 | Scalable, enterprise | Complex pricing, overkill | Rejected |
| Local Development | 5/10 | No cost | Not production-ready | Rejected |

**Rationale**: Hetzner CX31 provides 4x the specs at 25% the cost of DigitalOcean. EU-based for GDPR compliance. 12/mo (approximately $13) vs $48/mo for competitors.

---

## 5. Agent Team Structure

### Agent Alpha: Database Architect

**Codename**: ALPHA
**Mission**: Establish foundational PostgreSQL + pgvector database with unified content schema

**Priority**: CRITICAL BLOCKER (All other agents depend on this)

**Hours**: 1-2 hours

**Files to Create**:
```
backend/db/
├── __init__.py
├── connection.py           # SQLAlchemy engine with connection pooling
├── models.py               # Pydantic + SQLAlchemy hybrid models
├── schema.sql              # DDL for contents, authors, projects, patterns
└── migrations/
    ├── __init__.py
    └── 001_initial.sql     # Initial migration with vector indexes
```

**Training Documents**:
- `docs/pm/DATABASE_SCHEMA.md` (600 lines - complete schema specification)
- `docs/pm/PACKAGE_1_DATABASE_SETUP.md` (450 lines - step-by-step guide)
- pgvector documentation (ivfflat index, <=> operator)
- SQLAlchemy 2.0 async patterns

**Key Implementations**:
```sql
-- Vector similarity index (critical for performance)
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search index
CREATE INDEX idx_contents_fts ON contents
USING GIN(to_tsvector('english', content_body));

-- Platform filtering index
CREATE INDEX idx_contents_platform ON contents(platform);

-- Author grouping index
CREATE INDEX idx_contents_author ON contents(author_id);
```

**Success Criteria**:
- [ ] PostgreSQL 16 running on localhost:5432
- [ ] pgvector extension installed and enabled
- [ ] `unified_scraper` database created
- [ ] All 4 tables created (contents, authors, projects, patterns)
- [ ] Vector similarity search returns results in <500ms
- [ ] Insert 100 test rows in <1 second
- [ ] Connection pooling configured (10 connections, 20 overflow)

**Commit Template**:
```
feat(db): Setup PostgreSQL 16 with pgvector vector similarity

- Install PostgreSQL 16 + pgvector extension
- Create unified_scraper database
- Implement 4-table schema (contents, authors, projects, patterns)
- Configure ivfflat index for vector search (<=> cosine distance)
- Add FTS index for text search
- Setup SQLAlchemy 2.0 with async connection pooling
- Validate vector similarity query performance (<500ms)

Tables: contents (1536-dim vector), authors, projects, patterns
Indexes: ivfflat (cosine), GIN (FTS), B-tree (platform, author)
Pool: 10 connections, 20 overflow, 30s timeout

Ref: docs/pm/DATABASE_SCHEMA.md, Package 1
```

---

### Agent Beta: Twitter Scraper Specialist

**Codename**: BETA
**Mission**: Port IAC-024 enterprise Twitter scraping with anti-detection measures

**Priority**: HIGH (Core platform, reuses proven code)

**Hours**: 3-4 hours

**Files to Create**:
```
backend/scrapers/
├── __init__.py
├── base.py                           # BaseScraper abstract class
└── adapters/
    ├── __init__.py
    ├── twitter.py                    # Wrapper implementing BaseScraper
    ├── twitter_core.py               # Copy of persistent_x_session.py
    └── twitter_oauth.py              # Copy of playwright_oauth_client.py
data/
└── twitter_profile/                  # Browser profile persistence
    └── .gitkeep
tests/
└── scrapers/
    └── test_twitter.py               # Unit tests with mocks
```

**Source Code to Port**:
- `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py` (1,231 lines)
  - Advanced fingerprint spoofing (canvas, WebGL, audio context)
  - Human behavior simulation (curved mouse movements, typing variation)
  - Session health monitoring (rate limit detection, ban avoidance)
  - Adaptive rate limiting (exponential backoff with jitter)

- `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/playwright_oauth_client.py` (534 lines)
  - Google OAuth for @iamcodio account
  - Chrome profile persistence
  - Anti-detection measures (header spoofing, JS injection)

**Training Documents**:
- `docs/pm/IAC024_PORTING_STRATEGY.md` (450 lines - file-by-file porting guide)
- `docs/pm/API_SPECIFICATIONS.md` (Twitter endpoints section)
- IAC-024 source code (1,765 lines proven in production)

**Key Anti-Detection Features** (DO NOT MODIFY):
```python
# From persistent_x_session.py - PROVEN CODE
class PersistentXSession:
    def __init__(self):
        self._spoof_canvas_fingerprint()      # Randomize canvas API
        self._spoof_webgl_fingerprint()       # Fake GPU info
        self._spoof_audio_fingerprint()       # Unique audio context
        self._randomize_user_agent()          # Rotate UA strings
        self._inject_mouse_movement()         # Human cursor patterns
        self._add_typing_variation()          # Natural keystroke timing
        self._session_health_monitor()        # Detect rate limits
```

**Success Criteria**:
- [ ] Port 1,765 lines without logic modification
- [ ] BaseScraper wrapper interface implemented
- [ ] Scrape 10 tweets from @dankoe without ban
- [ ] Session persists across script restarts
- [ ] Human behavior simulation active (mouse, typing)
- [ ] Normalized data stored in PostgreSQL via UnifiedContent schema
- [ ] Unit tests pass with mocked Twitter responses

**Commit Template**:
```
feat(scrapers): Port IAC-024 Twitter scraper with enterprise anti-detection

- Copy persistent_x_session.py (1,231 lines anti-detection code)
- Copy playwright_oauth_client.py (534 lines OAuth fallback)
- Wrap in BaseScraper interface (extract, normalize, health_check)
- Test scraping @dankoe (10 tweets, zero bans)
- Persist session to data/twitter_profile/
- Store normalized data in PostgreSQL

Anti-detection: canvas spoofing, WebGL fake, human mouse curves
Fallback: Primary (session) → OAuth (Google) → ScraperAPI
Lines ported: 1,765 (100% from IAC-024 production code)

Ref: docs/pm/IAC024_PORTING_STRATEGY.md, Package 2
```

---

### Agent Gamma: API Engineer

**Codename**: GAMMA
**Mission**: Build FastAPI backend with universal scraping endpoints and job queue

**Priority**: HIGH (Central orchestration layer)

**Hours**: 2-3 hours

**Files to Create**:
```
backend/
├── __init__.py
├── main.py                           # FastAPI app entry point
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── scrape.py                 # POST /scrape endpoint
│   │   ├── query.py                  # POST /query/rag endpoint
│   │   └── generate.py               # POST /generate/course-script
│   └── middleware/
│       ├── __init__.py
│       ├── cors.py                   # CORS configuration
│       └── errors.py                 # Global error handling
├── services/
│   ├── __init__.py
│   ├── scraper_factory.py           # Platform routing factory
│   └── queue.py                      # Redis + RQ integration
└── config.py                         # Environment configuration
tests/
└── api/
    ├── test_scrape.py
    └── test_query.py
```

**Training Documents**:
- `docs/pm/API_SPECIFICATIONS.md` (700 lines - complete OpenAPI spec)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 3 section)
- FastAPI documentation (dependencies, routers, middleware)
- RQ documentation (Queue, Worker, retry strategies)

**Key Endpoints**:
```python
# POST /scrape - Universal scraping endpoint
@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest):
    """
    Scrape content from any supported platform.

    Args:
        platform: "twitter" | "youtube" | "reddit" | "web"
        target: Username, video_id, subreddit, or URL
        limit: Number of items to scrape (default 20)

    Returns:
        job_id: RQ job ID for async tracking
        estimated_time: Seconds until completion
    """
    scraper = ScraperFactory.get_scraper(request.platform)
    job = queue.enqueue(
        scraper.extract,
        request.target,
        request.limit,
        timeout='10m'
    )
    return {"job_id": job.id, "estimated_time": calculate_eta(request)}

# POST /query/rag - Semantic search endpoint
@router.post("/query/rag", response_model=RAGResponse)
async def query_rag(request: RAGRequest):
    """
    Semantic search across all scraped content.

    Args:
        query: Natural language query
        platforms: Filter by platforms (optional)
        limit: Max results (default 20)

    Returns:
        results: List of UnifiedContent with similarity scores
    """
    embedding = generate_embedding(request.query)
    results = chromadb_search(embedding, request.platforms, request.limit)
    return {"results": results}

# POST /generate/course-script - AI content generation
@router.post("/generate/course-script", response_model=CourseScriptResponse)
async def generate_course_script(request: CourseScriptRequest):
    """
    Generate production-ready course script from research.

    Args:
        topic: Course topic
        modules: Number of modules
        duration_per_module: Minutes per module
        sources: List of content_ids to synthesize

    Returns:
        script: Markdown formatted course script with citations
    """
    context = fetch_content_by_ids(request.sources)
    script = llm_generate_script(request.topic, context, request.modules)
    return {"script": script}
```

**Success Criteria**:
- [ ] FastAPI server runs on http://localhost:8000
- [ ] Swagger UI available at http://localhost:8000/docs
- [ ] POST /scrape returns job_id for async tracking
- [ ] POST /query/rag returns semantic search results
- [ ] POST /generate/course-script produces markdown output
- [ ] CORS configured for frontend access
- [ ] Global error handling with structured responses
- [ ] Redis + RQ worker processes jobs successfully
- [ ] Health check endpoint returns 200 OK

**Commit Template**:
```
feat(api): Create FastAPI backend with universal scraping endpoints

- FastAPI app with CORS middleware and error handling
- POST /scrape (platform factory pattern, async via RQ)
- POST /query/rag (ChromaDB semantic search)
- POST /generate/course-script (LLM synthesis)
- Scraper factory routing (Twitter, YouTube, Reddit, Web)
- Redis + RQ job queue with retry logic
- Swagger UI at /docs for API exploration
- Health check at GET /health

Endpoints: /scrape, /query/rag, /generate/course-script, /health
Queue: Redis + RQ (10m timeout, exponential backoff)
Factory: Dynamic scraper instantiation by platform

Ref: docs/pm/API_SPECIFICATIONS.md, Package 3
```

---

### Agent Delta: YouTube Scraper Specialist

**Codename**: DELTA
**Mission**: Extract YouTube transcripts with Whisper fallback for no-caption videos

**Priority**: MEDIUM (High-value content source)

**Hours**: 2-3 hours

**Files to Create**:
```
backend/scrapers/adapters/
├── youtube.py                        # Main scraper with fallback logic
└── youtube_whisper.py                # Whisper model integration
data/
└── youtube_cache/                    # Temporary audio files
    └── .gitkeep
tests/
└── scrapers/
    └── test_youtube.py               # Unit tests
```

**Training Documents**:
- `/Users/kjd/yt-agent-app/youtube-ai-analyzer-prd.md` (627 lines - Whisper patterns)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 4 section)
- youtube-transcript-api documentation
- yt-dlp documentation (audio extraction)
- OpenAI Whisper documentation (transcription)

**Pattern to Extract** (from yt-agent-app):
```python
class YouTubeScraper(BaseScraper):
    def extract(self, video_id: str) -> dict:
        # Primary: Official transcripts (instant)
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return self._parse_transcript(transcript, video_id)
        except TranscriptsDisabled:
            # Fallback: Whisper (2 min/video)
            return self._whisper_fallback(video_id)

    def _whisper_fallback(self, video_id: str) -> dict:
        # Download audio via yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'data/youtube_cache/{video_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}")

        # Transcribe with Whisper
        model = whisper.load_model("base")  # 74M params, fast
        result = model.transcribe(f"data/youtube_cache/{video_id}.wav")

        return {
            "video_id": video_id,
            "title": info['title'],
            "channel_name": info['uploader'],
            "transcript": result["text"],
            "view_count": info['view_count'],
            "like_count": info['like_count'],
            "upload_date": info['upload_date'],
            "duration": info['duration'],
            "source": "whisper"  # vs "official"
        }

    def normalize(self, raw_data: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="youtube",
            source_url=f"https://youtube.com/watch?v={raw_data['video_id']}",
            external_id=raw_data['video_id'],
            author_name=raw_data['channel_name'],
            content_type='video',
            title=raw_data['title'],
            body=raw_data['transcript'],
            published_at=parse_upload_date(raw_data['upload_date']),
            metrics={
                'views': raw_data['view_count'],
                'likes': raw_data['like_count'],
                'duration_seconds': raw_data['duration'],
            },
            metadata={
                'transcript_source': raw_data.get('source', 'official')
            }
        )
```

**Success Criteria**:
- [ ] Extract transcript from video WITH captions (instant)
- [ ] Fallback to Whisper for video WITHOUT captions (2 min)
- [ ] Metadata extracted (title, channel, views, likes, duration)
- [ ] Normalized to UnifiedContent schema
- [ ] Stored in PostgreSQL with embeddings
- [ ] Audio cache cleaned up after transcription
- [ ] Unit tests pass for both transcript sources

**Commit Template**:
```
feat(scrapers): Add YouTube scraper with Whisper fallback

- Primary: youtube-transcript-api (instant, official captions)
- Fallback: yt-dlp audio download + Whisper base model (2 min/video)
- Extract metadata: title, channel, views, likes, duration
- Normalize to UnifiedContent schema
- Cache audio temporarily in data/youtube_cache/
- Test videos with/without captions

Dependencies: youtube-transcript-api, yt-dlp, openai-whisper, ffmpeg
Whisper model: base (74M params, fast, sufficient quality)
Cost: $0 (local Whisper), uses CPU

Ref: yt-agent-app patterns, docs/pm/DAY2_WORK_PACKAGES.md Package 4
```

---

### Agent Epsilon: Reddit Scraper Specialist

**Codename**: EPSILON
**Mission**: Scrape Reddit posts using PRAW official API with rate limit compliance

**Priority**: MEDIUM (High-value VOC source)

**Hours**: 1-2 hours

**Files to Create**:
```
backend/scrapers/adapters/
└── reddit.py                         # PRAW integration
tests/
└── scrapers/
    └── test_reddit.py                # Unit tests
```

**Training Documents**:
- GitHub: JosephLai241/URS (Universal Reddit Scraper patterns)
- PRAW documentation (subreddit iteration, OAuth)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 5 section)
- Reddit API terms of service (rate limits)

**Key Implementation**:
```python
class RedditScraper(BaseScraper):
    def __init__(self, config: dict):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="UnifiedScraper/1.0 by /u/iamcodio"  # Required
        )
        self._last_request = 0
        self._request_count = 0

    def _respect_rate_limit(self):
        """OAuth: 1,000 requests per 10 minutes"""
        if self._request_count >= 1000:
            elapsed = time.time() - self._last_request
            if elapsed < 600:  # 10 minutes
                sleep_time = 600 - elapsed
                time.sleep(sleep_time)
            self._request_count = 0
            self._last_request = time.time()
        self._request_count += 1

    def extract(self, subreddit_name: str, limit: int = 50) -> list:
        self._respect_rate_limit()

        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        for post in subreddit.hot(limit=limit):
            posts.append({
                'id': post.id,
                'title': post.title,
                'body': post.selftext or "",
                'author': str(post.author) if post.author else "[deleted]",
                'subreddit': subreddit_name,
                'upvotes': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'url': post.url,
                'is_self': post.is_self,
            })

        return posts

    def normalize(self, raw_data: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="reddit",
            source_url=f"https://reddit.com/r/{raw_data['subreddit']}/comments/{raw_data['id']}",
            external_id=raw_data['id'],
            author_name=raw_data['author'],
            content_type='post',
            title=raw_data['title'],
            body=raw_data['body'],
            published_at=datetime.utcfromtimestamp(raw_data['created_utc']),
            metrics={
                'upvotes': raw_data['upvotes'],
                'upvote_ratio': raw_data['upvote_ratio'],
                'comments': raw_data['num_comments'],
            },
            metadata={
                'subreddit': raw_data['subreddit'],
                'is_self_post': raw_data['is_self'],
                'external_url': raw_data['url'] if not raw_data['is_self'] else None,
            }
        )
```

**Success Criteria**:
- [ ] PRAW OAuth configured with client_id and client_secret
- [ ] Scrape 50 posts from r/productivity
- [ ] Rate limit respected (1,000 req/10min)
- [ ] User-Agent string includes app name and version
- [ ] Normalized to UnifiedContent schema
- [ ] Stored in PostgreSQL
- [ ] Unit tests pass with mocked PRAW responses

**Commit Template**:
```
feat(scrapers): Add Reddit scraper using PRAW official API

- PRAW OAuth setup (client_id, client_secret, user_agent)
- Scrape subreddit posts (hot, limit=50)
- Strict rate limit compliance (1,000 req/10min OAuth)
- Extract: title, body, author, upvotes, comments, ratio
- Normalize to UnifiedContent schema
- Respectful User-Agent header

Dependencies: praw
Rate limit: 1,000/10min (OAuth), auto-sleep on threshold
Cost: $0 (official free API)

Ref: JosephLai241/URS patterns, docs/pm/DAY2_WORK_PACKAGES.md Package 5
```

---

### Agent Zeta: RAG Engineer

**Codename**: ZETA
**Mission**: Configure ChromaDB for semantic search with OpenAI embeddings

**Priority**: HIGH (Core intelligence feature)

**Hours**: 2-3 hours

**Files to Create**:
```
backend/services/
├── embeddings.py                     # OpenAI embedding generation
├── chromadb_client.py                # ChromaDB setup and persistence
└── rag_query.py                      # Semantic search implementation
data/
└── chromadb/                         # Persistent vector storage
    └── .gitkeep
tests/
└── services/
    └── test_rag.py                   # Unit tests
```

**Training Documents**:
- `docs/pm/DATABASE_SCHEMA.md` (embedding strategy section)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 6 section)
- ChromaDB documentation (persistence, HNSW algorithm)
- OpenAI Embeddings API documentation

**Key Implementation**:
```python
# backend/services/embeddings.py
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text: str) -> list[float]:
    """
    Generate 1536-dimensional embedding using OpenAI.

    Cost: $0.00002/1K tokens = $0.20 per 10K content items
    """
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",  # 1536 dims, cheapest
        input=text[:8000]  # Max 8192 tokens
    )
    return response.data[0].embedding

def batch_generate_embeddings(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Batch embedding for efficiency (100 at a time)."""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        embeddings.extend([d.embedding for d in response.data])
    return embeddings

# backend/services/chromadb_client.py
import chromadb
from chromadb.config import Settings

def get_chromadb_client():
    """Initialize ChromaDB with local persistence."""
    return chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./data/chromadb",  # NOT /tmp
        anonymized_telemetry=False
    ))

def get_collection(client):
    """Get or create unified content collection."""
    return client.get_or_create_collection(
        name="unified_content",
        metadata={
            "hnsw:space": "cosine",  # Cosine similarity
            "hnsw:construction_ef": 100,  # Construction quality
            "hnsw:search_ef": 50  # Search quality
        }
    )

def index_content(contents: list[UnifiedContent]):
    """Index content with embeddings in ChromaDB."""
    client = get_chromadb_client()
    collection = get_collection(client)

    texts = [c.body for c in contents]
    embeddings = batch_generate_embeddings(texts)

    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=[{
            "content_id": str(c.content_id),
            "platform": c.platform,
            "author": c.author_name,
            "title": c.title or "",
            "scraped_at": c.scraped_at.isoformat()
        } for c in contents],
        ids=[str(c.content_id) for c in contents]
    )

    client.persist()  # Save to disk

# backend/services/rag_query.py
def semantic_search(query: str, platforms: list[str] = None, limit: int = 20):
    """
    Search for semantically similar content.

    Args:
        query: Natural language search query
        platforms: Optional filter (["twitter", "youtube"])
        limit: Max results

    Returns:
        List of content with similarity scores
    """
    client = get_chromadb_client()
    collection = get_collection(client)

    query_embedding = generate_embedding(query)

    where_filter = None
    if platforms:
        where_filter = {"platform": {"$in": platforms}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    # Convert distances to similarity scores (1 - distance for cosine)
    return [
        {
            "content": doc,
            "metadata": meta,
            "similarity": 1 - dist  # Higher is better
        }
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )
    ]
```

**Success Criteria**:
- [ ] ChromaDB persists to `./data/chromadb/` (survives restarts)
- [ ] OpenAI embeddings generated (text-embedding-3-small)
- [ ] Batch embedding (100 items/request) for efficiency
- [ ] Semantic search returns results in <2 seconds
- [ ] Similarity scores > 0.7 for relevant queries
- [ ] Platform filtering works (twitter only, youtube only)
- [ ] Index 100 test items successfully
- [ ] Unit tests pass with mocked OpenAI responses

**Commit Template**:
```
feat(rag): Setup ChromaDB with OpenAI embeddings for semantic search

- ChromaDB with local persistence (./data/chromadb/)
- OpenAI text-embedding-3-small (1536 dims, $0.00002/1K tokens)
- Batch embedding generation (100/request for efficiency)
- HNSW algorithm with cosine similarity
- Semantic search with platform filtering
- Similarity threshold >0.7 for relevant results

Cost: $0.20 per 10K content items indexed
Speed: 100 embeddings = ~5 seconds (API call)
Persistence: DuckDB + Parquet (disk-based, not in-memory)

Ref: docs/pm/DATABASE_SCHEMA.md, Package 6
```

---

### Agent Eta: DevOps Engineer

**Codename**: ETA
**Mission**: Configure CI/CD pipeline with GitHub Actions and Hetzner deployment

**Priority**: HIGH (Ensures code quality and automated deployment)

**Hours**: 2-3 hours

**Files to Create**:
```
.github/
└── workflows/
    └── ci-cd.yml                     # Main pipeline
podman-compose.yml                    # Container orchestration
Dockerfile                            # Core engine container
scrapers/
├── twitter/
│   └── Dockerfile
├── youtube/
│   └── Dockerfile
├── reddit/
│   └── Dockerfile
└── web/
    └── Dockerfile
scripts/
├── deploy.sh                         # Hetzner deployment script
├── setup_hetzner.sh                  # Initial server setup
└── health_check.sh                   # Container health monitoring
.env.example                          # Environment template
```

**Training Documents**:
- `docs/ci-setup/GITHUB_ACTIONS_RESEARCH_2025.md` (current best practices)
- `docs/ci-setup/AUTOMATION_GUIDE.md` (workflow templates)
- `docs/ci-setup/QUICK_START.md` (5-minute setup)
- `docs/pm/ARCHITECTURE_PROPOSAL.md` (deployment section)
- Podman documentation (rootless containers)
- GitHub Actions documentation (secrets, environments)

**GitHub Actions Workflow**:
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'
  PODMAN_VERSION: '4.0'

jobs:
  # Gate 1: Code Quality
  lint:
    name: Code Quality Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install linters
        run: pip install ruff mypy
      - name: Run Ruff (Python linter)
        run: ruff check .
      - name: Run MyPy (type checker)
        run: mypy --ignore-missing-imports backend/

  # Gate 2: Unit Tests
  test:
    name: Unit Tests
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests with coverage
        run: pytest tests/ -v --cov=backend --cov-report=xml --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  # Gate 3: Build Verification
  build:
    name: Build Containers
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Podman
        run: |
          sudo apt-get update
          sudo apt-get install -y podman
      - name: Build core engine
        run: podman build -t unified_scraper_core ./backend
      - name: Build Twitter module
        run: podman build -t unified_scraper_twitter ./scrapers/twitter
      - name: Build YouTube module
        run: podman build -t unified_scraper_youtube ./scrapers/youtube
      - name: Build Reddit module
        run: podman build -t unified_scraper_reddit ./scrapers/reddit
      - name: Verify builds
        run: podman images | grep unified_scraper

  # Gate 4: Integration Tests
  integration:
    name: Integration Tests
    needs: build
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: pytest tests/integration/ -v

  # Gate 5: Security Scan
  security:
    name: Security Scan
    needs: integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
      - name: Check for secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # Final: Deploy to Hetzner
  deploy:
    name: Deploy to Production
    needs: security
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Hetzner
        env:
          HETZNER_SSH_KEY: ${{ secrets.HETZNER_SSH_KEY }}
          HETZNER_HOST: ${{ secrets.HETZNER_HOST }}
        run: |
          echo "$HETZNER_SSH_KEY" > /tmp/hetzner_key
          chmod 600 /tmp/hetzner_key
          ssh -i /tmp/hetzner_key -o StrictHostKeyChecking=no root@$HETZNER_HOST << 'EOF'
            cd /opt/unified_scraper
            git pull origin main
            podman-compose down
            podman-compose up -d --build
            podman ps
            curl -f http://localhost:8000/health || exit 1
          EOF
```

**Success Criteria**:
- [ ] GitHub Actions workflow file created and valid
- [ ] 5 gates configured (lint, test, build, integration, security)
- [ ] Podman-compose.yml orchestrates all containers
- [ ] All Dockerfiles build without errors
- [ ] Hetzner SSH deployment script works
- [ ] Health check endpoint validates deployment
- [ ] Secrets configured in GitHub (HETZNER_SSH_KEY, HETZNER_HOST)
- [ ] .env.example documents all required variables
- [ ] Zero manual intervention after git push to main

**Commit Template**:
```
feat(devops): Configure CI/CD pipeline with GitHub Actions and Hetzner

- GitHub Actions workflow with 5 quality gates
- Gate 1: Ruff linting + MyPy type checking
- Gate 2: Pytest unit tests (80% coverage minimum)
- Gate 3: Podman container builds (all modules)
- Gate 4: Integration tests with real PostgreSQL + Redis
- Gate 5: Trivy security scan + GitLeaks secret detection
- Automated Hetzner deployment on main branch push
- Podman-compose.yml for container orchestration
- Health check validation post-deployment

Pipeline: lint → test → build → integration → security → deploy
Containers: postgres, redis, chromadb, core, twitter, youtube, reddit
Deployment: SSH + git pull + podman-compose up --build

Ref: docs/ci-setup/, docs/pm/ARCHITECTURE_PROPOSAL.md
```

---

## 6. Risk Assessment

### Critical Failure Points (Top 10)

| # | Risk | Probability | Impact | Mitigation | Fallback |
|---|------|-------------|--------|------------|----------|
| 1 | **PostgreSQL + pgvector setup fails** | LOW | CRITICAL | Use official pgvector/pgvector:pg16 Docker image | SQLite + sqlite-vss (degrade to local-only) |
| 2 | **Twitter bans IAC-024 scraper** | MEDIUM | HIGH | Use 100% proven code without modifications, test with throwaway account first | ScraperAPI structured endpoint ($0.0024/tweet) |
| 3 | **OpenAI API rate limits** | LOW | MEDIUM | Batch requests (100/batch), implement exponential backoff | Use sentence-transformers locally (lower quality) |
| 4 | **Container networking issues** | MEDIUM | HIGH | Use Podman pod (shared network namespace), test locally first | Host networking mode (--net=host) |
| 5 | **Redis connection drops** | LOW | MEDIUM | Connection pooling, retry logic, health monitoring | In-memory queue (lose persistence) |
| 6 | **Hetzner SSH deployment fails** | LOW | HIGH | Test SSH key manually, use GitHub environment protection rules | Manual deployment via SSH |
| 7 | **ChromaDB memory exhaustion** | MEDIUM | MEDIUM | Monitor memory usage, set limits, use HNSW ef parameters wisely | Restart container, reduce index size |
| 8 | **PRAW OAuth credentials expire** | LOW | LOW | Store refresh token, auto-renew | Create new Reddit app credentials |
| 9 | **YouTube transcript API changes** | LOW | MEDIUM | Version pin youtube-transcript-api, monitor for breaking changes | Whisper fallback (already implemented) |
| 10 | **GitHub Actions runner timeout** | LOW | MEDIUM | Split jobs, cache dependencies, optimize test parallelization | Local testing + manual deploy |

### Risk Severity Matrix

```
                    IMPACT
              Low       Medium      High       Critical
         ┌─────────┬──────────┬──────────┬──────────┐
    High │    -    │    -     │    -     │    -     │
         ├─────────┼──────────┼──────────┼──────────┤
  Medium │    -    │   #7     │  #2, #4  │    -     │
P        ├─────────┼──────────┼──────────┼──────────┤
R    Low │   #8    │  #3, #9  │  #6, #10 │   #1     │
O        │         │   #5     │          │          │
B        └─────────┴──────────┴──────────┴──────────┘
```

### Risk Mitigation Budget

| Risk Category | Hours Reserved | Contingency Actions |
|---------------|----------------|---------------------|
| Database Setup | 1 hour | Docker image pre-pull, schema validation script |
| Twitter Scraping | 2 hours | Test account creation, rate limit monitoring |
| API Integration | 1 hour | Mock server for testing, circuit breaker pattern |
| Deployment | 1 hour | Manual deployment guide, rollback script |
| **Total Buffer** | **5 hours** | Added to 6-7 hour estimate = 11-12 hours worst case |

---

## 7. Cost Analysis

### Monthly Operational Costs

| Service | Plan | Cost/Month | Usage Included | Overage |
|---------|------|------------|----------------|---------|
| **Jina.ai Reader** | FREE | $0 | 50K pages | N/A (hard limit) |
| **ScraperAPI** | Hobby (fallback) | $0-49 | 100K credits | $0.0005/credit |
| **OpenAI Embeddings** | Pay-as-you-go | $20 | ~1M tokens | $0.00002/1K tokens |
| **OpenAI GPT-4** | Pay-as-you-go | $10 | ~100K analysis tokens | $0.0025/1K input |
| **Hetzner VPS** | CX31 | $13 | 4 vCPU, 8GB RAM | N/A |
| **PostgreSQL** | Self-hosted | $0 | Unlimited | N/A |
| **Redis** | Self-hosted | $0 | Unlimited | N/A |
| **ChromaDB** | Self-hosted | $0 | Unlimited | N/A |
| **GitHub Actions** | FREE (public repo) | $0 | 2,000 min/month | $0.008/min |
| **TOTAL** | | **$43-92/mo** | | |

### Cost Comparison vs Competitors

| Service | Monthly Cost | Platforms | Pattern Detection | RAG Search | Course Scripts |
|---------|--------------|-----------|-------------------|------------|----------------|
| **IAC-032 (Us)** | **$43-92** | Twitter, YouTube, Reddit, Web, Amazon | **YES** | **YES** | **YES** |
| TweetHunter | $49-99 | Twitter only | NO | NO | NO |
| SuperX | $29 | Twitter only | NO | NO | NO |
| Hypefury | $19-49 | Twitter only | NO | NO | NO |
| Hootsuite | $99-249 | Multi (scheduling only) | NO | NO | NO |
| BuzzSumo | $99-299 | Web content only | NO | NO | NO |

**Competitive Advantages**:
- **70% cheaper** than BuzzSumo for multi-platform
- **Same price** as TweetHunter but 4x more platforms
- **Unique features**: Pattern detection, RAG search, course generation
- **No vendor lock-in**: Self-hosted, open source

### Cost Optimization Strategies

1. **FREE Tier First**: Jina.ai (50K/mo), PRAW (FREE), youtube-transcript-api (FREE)
2. **ScraperAPI Fallback Only**: Use only for Twitter JS rendering
3. **Batch Embeddings**: 100/request reduces API overhead
4. **Cache Results**: Store in PostgreSQL, avoid re-scraping
5. **Monitor Usage**: Dashboard for credits tracking

### Break-Even Analysis

**Investment**:
- Development: 6-7 hours (CCW agents)
- Research: Already complete (20K+ lines docs)
- Infrastructure setup: 2 hours

**ROI Timeline**:
- Month 1: $92 operational cost
- Month 2: $92 operational cost
- Month 3: $92 operational cost
- **Total 3-month cost**: $276

**Savings vs TweetHunter** (for multi-platform):
- TweetHunter: $99/mo × 3 = $297
- **Us**: $92/mo × 3 = $276
- **Savings**: $21 + 4x more platforms + unique features

**Value Generated**:
- Time saved: 10+ hours/week research → 30 min/week
- Content quality: Data-driven vs intuition
- Competitive intelligence: Cross-platform patterns

---

## 8. Implementation Timeline

### Phase 1: Foundation (Sequential)

**Duration**: 1-2 hours
**Agent**: ALPHA (Database Architect)
**Blocks**: All other agents

```
Hour 0 → Hour 2
┌──────────────────────────────────────────┐
│  ALPHA: PostgreSQL + pgvector Setup     │
│  - Install PostgreSQL 16                 │
│  - Enable pgvector extension             │
│  - Create unified_scraper database       │
│  - Execute schema.sql (4 tables)         │
│  - Create vector indexes                 │
│  - Test similarity search                │
│  - Configure connection pooling          │
└──────────────────────────────────────────┘
                    │
                    ▼
            DATABASE READY
        (All agents can proceed)
```

### Phase 2: Parallel Execution (Simultaneous)

**Duration**: 3-4 hours (longest agent determines total)
**Agents**: BETA, GAMMA, DELTA, EPSILON, ZETA, ETA
**Dependencies**: All require ALPHA completion

```
Hour 2 → Hour 6 (MAX of all durations)

BETA (Twitter)         ████████████████ 3-4h
GAMMA (API)            ████████████ 2-3h
DELTA (YouTube)        ████████████ 2-3h
EPSILON (Reddit)       ████████ 1-2h
ZETA (RAG)             ████████████ 2-3h
ETA (DevOps)           ████████████ 2-3h
```

### Phase 3: Integration (Sequential)

**Duration**: 1 hour
**Activity**: Cross-module testing and validation

```
Hour 6 → Hour 7
┌──────────────────────────────────────────┐
│  INTEGRATION TESTING                     │
│  - All modules communicate               │
│  - End-to-end scrape → store → search   │
│  - CI/CD pipeline green                  │
│  - Deploy to Hetzner                     │
│  - Validate health checks                │
└──────────────────────────────────────────┘
                    │
                    ▼
              MVP COMPLETE
```

### Total Timeline Summary

| Phase | Duration | Critical Path |
|-------|----------|---------------|
| Phase 1: Foundation | 1-2 hours | ALPHA (blocker) |
| Phase 2: Parallel | 3-4 hours | BETA (longest) |
| Phase 3: Integration | 1 hour | All agents |
| **TOTAL** | **6-7 hours** | **Sequential execution** |

**Best Case**: 6 hours (all agents complete quickly)
**Worst Case**: 7 hours + 5 hours buffer = 12 hours (with issues)
**Realistic Estimate**: 7 hours total execution time

### Gantt Chart Visualization

```
Time (hours)  0    1    2    3    4    5    6    7
              │    │    │    │    │    │    │    │
ALPHA         ████████
BETA               │    ████████████████████
GAMMA              │    ████████████████
DELTA              │    ████████████████
EPSILON            │    ████████████
ZETA               │    ████████████████
ETA                │    ████████████████
INTEGRATION        │                        │    ████
                   │                        │    │
              ─────┴────────────────────────┴────┴────
              Phase 1    Phase 2            Phase 3
```

---

## 9. Deployment Strategy

### Production Environment: Hetzner VPS

**Server Specification**: CX31
- 4 vCPU (AMD EPYC)
- 8 GB RAM
- 80 GB SSD NVMe
- 20 TB Traffic/month
- Ubuntu 22.04 LTS
- **Cost**: 12.49/month (~$13)

**Resource Allocation**:
```
Total RAM: 8 GB
┌─────────────────────────────┐
│ PostgreSQL + pgvector       │ 2 GB
│ Redis 7                     │ 256 MB
│ ChromaDB                    │ 1 GB
│ FastAPI Core Engine         │ 512 MB
│ Twitter Module              │ 500 MB
│ YouTube Module              │ 500 MB
│ Reddit Module               │ 200 MB
│ Web Module                  │ 200 MB
│ System + Buffer             │ 2.8 GB
└─────────────────────────────┘
```

### Initial Server Setup Script

```bash
#!/bin/bash
# scripts/setup_hetzner.sh

# Update system
apt update && apt upgrade -y

# Install Podman (rootless containers)
apt install -y podman podman-compose

# Install Git
apt install -y git

# Install monitoring tools
apt install -y htop ncdu

# Configure firewall
ufw allow 22/tcp    # SSH
ufw allow 8000/tcp  # FastAPI
ufw enable

# Create application user
useradd -m -s /bin/bash scraper
usermod -aG sudo scraper

# Clone repository
su - scraper << 'EOF'
git clone https://github.com/iamcodio/IAC-032-unified-scraper.git /opt/unified_scraper
cd /opt/unified_scraper

# Create data directories
mkdir -p data/{postgres,redis,chromadb,twitter_profile,youtube_cache}

# Copy environment file
cp .env.example .env
# IMPORTANT: Edit .env with actual credentials

# Pull pre-built images
podman pull pgvector/pgvector:pg16
podman pull redis:7-alpine
podman pull chromadb/chroma:latest
EOF

echo "Server setup complete. Edit /opt/unified_scraper/.env with credentials."
```

### Podman Compose Configuration

```yaml
# podman-compose.yml
version: "3.8"

services:
  # Infrastructure Layer
  postgres:
    image: pgvector/pgvector:pg16
    container_name: unified_scraper_db
    restart: always
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: unified_scraper
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scraper"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: unified_scraper_queue
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  chromadb:
    image: chromadb/chroma:latest
    container_name: unified_scraper_rag
    restart: always
    ports:
      - "8001:8000"
    volumes:
      - ./data/chromadb:/chroma/chroma
    environment:
      ANONYMIZED_TELEMETRY: "false"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Application Layer
  core_engine:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: unified_scraper_core
    restart: always
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://scraper:${DB_PASSWORD}@postgres:5432/unified_scraper
      REDIS_URL: redis://redis:6379
      CHROMADB_URL: http://chromadb:8000
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LOG_LEVEL: INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Scraper Modules
  twitter_scraper:
    build:
      context: ./scrapers/twitter
      dockerfile: Dockerfile
    container_name: unified_scraper_twitter
    restart: always
    ports:
      - "8010:8000"
    environment:
      SCRAPER_API_KEY: ${SCRAPER_API_KEY}
      CORE_ENGINE_URL: http://core_engine:8000
    volumes:
      - ./data/twitter_profile:/app/data/profile
    depends_on:
      - core_engine

  youtube_scraper:
    build:
      context: ./scrapers/youtube
      dockerfile: Dockerfile
    container_name: unified_scraper_youtube
    restart: always
    ports:
      - "8020:8000"
    environment:
      CORE_ENGINE_URL: http://core_engine:8000
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./data/youtube_cache:/app/data/cache
    depends_on:
      - core_engine

  reddit_scraper:
    build:
      context: ./scrapers/reddit
      dockerfile: Dockerfile
    container_name: unified_scraper_reddit
    restart: always
    ports:
      - "8030:8000"
    environment:
      REDDIT_CLIENT_ID: ${REDDIT_CLIENT_ID}
      REDDIT_CLIENT_SECRET: ${REDDIT_CLIENT_SECRET}
      CORE_ENGINE_URL: http://core_engine:8000
    depends_on:
      - core_engine

  web_scraper:
    build:
      context: ./scrapers/web
      dockerfile: Dockerfile
    container_name: unified_scraper_web
    restart: always
    ports:
      - "8040:8000"
    environment:
      JINA_API_KEY: ${JINA_API_KEY}
      SCRAPER_API_KEY: ${SCRAPER_API_KEY}
      CORE_ENGINE_URL: http://core_engine:8000
    depends_on:
      - core_engine

networks:
  default:
    name: unified_scraper_network
```

### Zero-Downtime Deployment

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "Starting zero-downtime deployment..."

# Navigate to project
cd /opt/unified_scraper

# Pull latest code
git pull origin main

# Build new containers without stopping old ones
podman-compose build

# Rolling restart (one at a time)
for service in core_engine twitter_scraper youtube_scraper reddit_scraper web_scraper; do
    echo "Restarting $service..."
    podman-compose stop $service
    podman-compose up -d $service

    # Wait for health check
    sleep 10
    if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Health check failed for $service. Rolling back..."
        git checkout HEAD~1
        podman-compose up -d $service
        exit 1
    fi
done

# Verify all containers running
podman ps | grep unified_scraper

echo "Deployment complete!"
```

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/${DATE}"

mkdir -p $BACKUP_DIR

# PostgreSQL backup
podman exec unified_scraper_db pg_dump -U scraper unified_scraper > \
    ${BACKUP_DIR}/postgres_dump.sql

# Redis backup (RDB snapshot)
podman exec unified_scraper_queue redis-cli BGSAVE
cp ./data/redis/dump.rdb ${BACKUP_DIR}/redis_dump.rdb

# ChromaDB backup (entire data directory)
tar -czf ${BACKUP_DIR}/chromadb_backup.tar.gz ./data/chromadb/

# Cleanup old backups (keep 7 days)
find /opt/backups -type d -mtime +7 -exec rm -rf {} +

echo "Backup complete: ${BACKUP_DIR}"
```

---

## 10. CI/CD Pipeline

### Pipeline Architecture (5 Gates)

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GATE 1: CODE QUALITY                                       │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Ruff Linter  │  │ MyPy Types   │                        │
│  │ (style)      │  │ (safety)     │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         └─────────┬────────┘                               │
│                   ▼                                         │
│  GATE 2: UNIT TESTS                                        │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Pytest       │  │ Coverage     │                        │
│  │ (>80%)       │  │ Report       │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         └─────────┬────────┘                               │
│                   ▼                                         │
│  GATE 3: BUILD VERIFICATION                                │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Podman Build │  │ Health Check │                        │
│  │ (all images) │  │ (containers) │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         └─────────┬────────┘                               │
│                   ▼                                         │
│  GATE 4: INTEGRATION TESTS                                 │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Real DB      │  │ API Contract │                        │
│  │ (PostgreSQL) │  │ (OpenAPI)    │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         └─────────┬────────┘                               │
│                   ▼                                         │
│  GATE 5: SECURITY SCAN                                     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Trivy CVE    │  │ GitLeaks     │                        │
│  │ (containers) │  │ (secrets)    │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         └─────────┬────────┘                               │
│                   ▼                                         │
│  ┌────────────────────────────────────┐                    │
│  │         DEPLOY TO HETZNER          │                    │
│  │  (Only on main branch push)        │                    │
│  └────────────────────────────────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Gate Specifications

**Gate 1: Code Quality**
- **Ruff**: Python linter, checks PEP8, imports, complexity
- **MyPy**: Static type checker, ensures type safety
- **Pass Criteria**: Zero errors, warnings treated as errors
- **Failure Action**: Return to agent for fixes

**Gate 2: Unit Tests**
- **Pytest**: Test runner with fixtures and mocks
- **Coverage**: Minimum 80% code coverage
- **Pass Criteria**: All tests green, coverage threshold met
- **Failure Action**: Add missing tests or fix code

**Gate 3: Build Verification**
- **Podman Build**: Compile all container images
- **Health Checks**: Containers respond to health endpoints
- **Pass Criteria**: All images build, health checks 200 OK
- **Failure Action**: Fix Dockerfile or dependencies

**Gate 4: Integration Tests**
- **Real Database**: PostgreSQL + pgvector service
- **API Contracts**: Validate OpenAPI schema compliance
- **Pass Criteria**: End-to-end flows work, contracts match
- **Failure Action**: Fix service integration issues

**Gate 5: Security Scan**
- **Trivy**: Container CVE vulnerability scanner
- **GitLeaks**: Secret detection in code
- **Pass Criteria**: No CRITICAL/HIGH CVEs, no secrets
- **Failure Action**: Update vulnerable dependencies, remove secrets

### GitHub Secrets Configuration

```bash
# Required secrets in GitHub repository settings

# Hetzner deployment
HETZNER_SSH_KEY: (base64 encoded private key)
HETZNER_HOST: your-hetzner-ip.com

# API keys (for integration tests)
OPENAI_API_KEY: sk-proj-...
SCRAPER_API_KEY: ...
REDDIT_CLIENT_ID: ...
REDDIT_CLIENT_SECRET: ...
JINA_API_KEY: jina_...

# Database
DB_PASSWORD: (secure random string)

# Optional
CODECOV_TOKEN: (for coverage reports)
```

### Pipeline Performance Targets

| Gate | Target Duration | Max Duration | Parallel Jobs |
|------|----------------|--------------|---------------|
| Lint | 30 seconds | 1 minute | 2 |
| Unit Tests | 2 minutes | 5 minutes | 1 |
| Build | 5 minutes | 10 minutes | 4 |
| Integration | 3 minutes | 10 minutes | 1 |
| Security | 1 minute | 3 minutes | 2 |
| **Total** | **11.5 minutes** | **29 minutes** | **Sequential** |

### Rollback Strategy

```bash
# Automated rollback on deployment failure
if ! curl -f http://localhost:8000/health; then
    git checkout HEAD~1  # Previous commit
    podman-compose up -d --build

    # Notify team
    curl -X POST $SLACK_WEBHOOK -d '{
        "text": "Deployment failed, rolled back to previous version"
    }'
fi
```

---

## 11. Success Criteria

### MVP Definition of Done (Day 3)

#### Infrastructure Checklist

- [ ] **PostgreSQL 16 + pgvector running**
  - Database: `unified_scraper`
  - Extension: `CREATE EXTENSION vector;` enabled
  - Tables: contents, authors, projects, patterns
  - Indexes: ivfflat (vector), GIN (FTS), B-tree (platform)
  - Performance: Vector search <500ms

- [ ] **Redis 7 queue operational**
  - Persistence: AOF enabled
  - Jobs: Enqueue/dequeue working
  - Monitoring: Queue length trackable

- [ ] **ChromaDB RAG store**
  - Persistence: `./data/chromadb/` survives restarts
  - Collection: `unified_content` created
  - Algorithm: HNSW with cosine similarity
  - Performance: Semantic search <2 seconds

- [ ] **All containers healthy**
  - Count: 7+ containers (`podman ps`)
  - Health: All respond 200 OK
  - Networking: Inter-container communication working
  - Logs: No critical errors

#### API Endpoint Checklist

- [ ] **POST /scrape**
  - Twitter: Scrape 100 tweets from @dankoe
  - YouTube: Extract transcript from video ID
  - Reddit: Fetch 50 posts from r/productivity
  - Web: Scrape blog article via Jina.ai
  - Response: Returns job_id for async tracking

- [ ] **POST /query/rag**
  - Query: "What does Dan Koe say about focus?"
  - Results: Returns top 20 semantically similar items
  - Filtering: Can filter by platform
  - Performance: <2 seconds response time

- [ ] **POST /analyze/patterns**
  - Detection: Cross-platform elaboration patterns
  - Similarity: Threshold >0.85 for related content
  - Output: Timeline of concept evolution

- [ ] **POST /generate/course-script**
  - Input: Project brief, target modules
  - Output: Markdown formatted course script
  - Citations: Includes source URLs
  - Quality: Production-ready (minimal editing needed)

- [ ] **GET /health**
  - Status: 200 OK
  - Body: `{"status": "healthy", "uptime": "...", "version": "1.0.0"}`

#### Data Quality Checklist

- [ ] **Unified content schema**
  - All platforms normalize to same structure
  - Vector embeddings: 1536 dimensions
  - Metrics tracked: likes, views, engagement
  - Analysis: Framework detection working

- [ ] **Authority detection**
  - Ranking: Follower count x engagement x quality
  - Top influencers: Correctly identified
  - Insights: Actionable intelligence generated

- [ ] **Content gap analysis**
  - SERP vs authorities: Gaps identified
  - Opportunities: Underserved topics highlighted
  - Recommendations: Specific action items

#### Code Quality Checklist

- [ ] **Modular adapter pattern**
  - New platform: Add in 30 minutes
  - Interface: BaseScraper contract enforced
  - Isolation: Modules don't share state

- [ ] **Type safety**
  - Pydantic models: All data validated
  - MyPy: Zero type errors
  - IDE support: Full autocompletion

- [ ] **Clean architecture**
  - Separation: Frontend <- API <- Services <- Scrapers
  - Dependencies: Injected, not hardcoded
  - Testing: Easy to mock external services

- [ ] **Error handling**
  - Retry logic: Exponential backoff with jitter
  - Circuit breaker: Fail fast on persistent errors
  - Logging: Structured JSON logs

#### CI/CD Checklist

- [ ] **Pipeline green**
  - Lint: Ruff passes
  - Types: MyPy passes
  - Tests: >80% coverage
  - Build: All containers compile
  - Security: No CRITICAL CVEs

- [ ] **Automated deployment**
  - Trigger: Push to main branch
  - Action: SSH to Hetzner, pull, rebuild
  - Validation: Health check passes
  - Rollback: Automatic on failure

- [ ] **Zero manual intervention**
  - Code review: Automated checks sufficient
  - Deployment: No SSH required manually
  - Monitoring: Alerts configured

#### Performance Benchmarks

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Scrape 100 tweets | <5 min | <10 min | >15 min |
| Semantic search | <2 sec | <5 sec | >10 sec |
| Embedding generation (100 items) | <10 sec | <30 sec | >60 sec |
| Course script generation | <60 sec | <120 sec | >300 sec |
| Container startup (all) | <30 sec | <60 sec | >120 sec |
| CI/CD pipeline | <15 min | <30 min | >45 min |

---

## Appendix A: API Specifications

### OpenAPI 3.0 Schema (Excerpt)

```yaml
openapi: 3.0.3
info:
  title: Unified Scraper API
  version: 1.0.0
  description: Multi-platform content intelligence engine

servers:
  - url: http://localhost:8000
    description: Development server
  - url: https://api.unifiedscraper.com
    description: Production server

paths:
  /scrape:
    post:
      summary: Scrape content from any supported platform
      operationId: scrapeContent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ScrapeRequest'
      responses:
        '202':
          description: Job queued successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScrapeResponse'
        '400':
          description: Invalid request
        '429':
          description: Rate limit exceeded
        '500':
          description: Internal server error

  /query/rag:
    post:
      summary: Semantic search across all content
      operationId: queryRAG
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RAGRequest'
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RAGResponse'

  /health:
    get:
      summary: Service health check
      operationId: healthCheck
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'

components:
  schemas:
    ScrapeRequest:
      type: object
      required:
        - platform
        - target
      properties:
        platform:
          type: string
          enum: [twitter, youtube, reddit, web]
        target:
          type: string
          description: Username, video_id, subreddit, or URL
        limit:
          type: integer
          default: 20
          minimum: 1
          maximum: 100

    ScrapeResponse:
      type: object
      properties:
        job_id:
          type: string
          format: uuid
        estimated_time:
          type: integer
          description: Seconds until completion
        status_url:
          type: string
          format: uri

    RAGRequest:
      type: object
      required:
        - query
      properties:
        query:
          type: string
          description: Natural language search query
        platforms:
          type: array
          items:
            type: string
          description: Filter by platforms
        limit:
          type: integer
          default: 20

    RAGResponse:
      type: object
      properties:
        results:
          type: array
          items:
            $ref: '#/components/schemas/ContentResult'
        total:
          type: integer

    ContentResult:
      type: object
      properties:
        content_id:
          type: string
          format: uuid
        platform:
          type: string
        title:
          type: string
        body:
          type: string
        similarity:
          type: number
          format: float
        source_url:
          type: string
          format: uri

    HealthResponse:
      type: object
      properties:
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        uptime:
          type: string
        version:
          type: string
        components:
          type: object
          properties:
            database:
              type: string
            queue:
              type: string
            rag:
              type: string
```

---

## Appendix B: Database Schema

### Complete SQL DDL

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main content table
CREATE TABLE contents (
    content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    source_url TEXT UNIQUE NOT NULL,
    external_id VARCHAR(255),

    -- Author information
    author_id VARCHAR(255),
    author_name VARCHAR(255),
    author_handle VARCHAR(255),

    -- Content data
    content_type VARCHAR(50),  -- tweet, video, post, article
    title TEXT,
    body TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,

    -- Metrics (JSONB for flexibility)
    metrics JSONB DEFAULT '{}'::jsonb,
    -- Example: {"likes": 100, "views": 5000, "comments": 25}

    -- LLM Analysis (JSONB for flexibility)
    analysis JSONB DEFAULT '{}'::jsonb,
    -- Example: {"hooks": [...], "framework": "AIDA", "themes": [...]}

    -- Vector embedding (1536 dimensions for OpenAI)
    embedding vector(1536),

    -- Metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_platform CHECK (platform IN ('twitter', 'youtube', 'reddit', 'web', 'amazon'))
);

-- Authors table (denormalized for analytics)
CREATE TABLE authors (
    author_id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    handle VARCHAR(255),

    -- Profile metrics
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,

    -- Calculated authority score
    authority_score FLOAT DEFAULT 0.0,

    -- Timestamps
    first_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Additional profile data
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Research projects table
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Project configuration
    config JSONB DEFAULT '{}'::jsonb,
    -- Example: {"topic": "focus systems", "platforms": ["twitter", "youtube"]}

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cross-platform patterns table
CREATE TABLE patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL,  -- elaboration, repurpose, series

    -- Source content
    source_content_id UUID REFERENCES contents(content_id),
    source_platform VARCHAR(50),
    source_date TIMESTAMP WITH TIME ZONE,

    -- Related content
    related_content_id UUID REFERENCES contents(content_id),
    related_platform VARCHAR(50),
    related_date TIMESTAMP WITH TIME ZONE,

    -- Pattern metrics
    similarity_score FLOAT,
    confidence FLOAT,

    -- Analysis
    insight TEXT,

    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_contents_platform ON contents(platform);
CREATE INDEX idx_contents_author ON contents(author_id);
CREATE INDEX idx_contents_published ON contents(published_at DESC);
CREATE INDEX idx_contents_scraped ON contents(scraped_at DESC);

-- Vector similarity index (critical for RAG performance)
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search index
CREATE INDEX idx_contents_fts ON contents
USING GIN(to_tsvector('english', body));

-- Combined text search on title + body
CREATE INDEX idx_contents_title_fts ON contents
USING GIN(to_tsvector('english', COALESCE(title, '') || ' ' || body));

-- Author indexes
CREATE INDEX idx_authors_authority ON authors(authority_score DESC);
CREATE INDEX idx_authors_platform ON authors(platform);

-- Pattern indexes
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_source ON patterns(source_content_id);
CREATE INDEX idx_patterns_similarity ON patterns(similarity_score DESC);
```

---

## Appendix C: Environment Variables

### Complete .env.example

```bash
# ======================
# DATABASE CONFIGURATION
# ======================
# PostgreSQL connection
DATABASE_URL=postgresql://scraper:YOUR_PASSWORD@localhost:5432/unified_scraper
DB_PASSWORD=YOUR_SECURE_PASSWORD
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Redis connection
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=20

# ChromaDB connection
CHROMADB_URL=http://localhost:8001
CHROMADB_PERSIST_DIR=./data/chromadb

# ======================
# SCRAPING SERVICES
# ======================
# ScraperAPI (fallback, $49/mo)
SCRAPER_API_KEY=YOUR_SCRAPER_API_KEY
SCRAPER_API_TIMEOUT=60

# Jina.ai Reader (FREE tier, 50K/mo)
JINA_API_KEY=jina_YOUR_KEY

# Twitter (IAC-024 credentials)
TWITTER_USERNAME=iamcodio
TWITTER_PASSWORD=YOUR_PASSWORD
TWITTER_PROFILE_DIR=./data/twitter_profile

# Reddit (PRAW OAuth)
REDDIT_CLIENT_ID=YOUR_CLIENT_ID
REDDIT_CLIENT_SECRET=YOUR_CLIENT_SECRET
REDDIT_USER_AGENT=UnifiedScraper/1.0 by /u/iamcodio

# ======================
# LLM SERVICES
# ======================
# OpenAI (embeddings + bulk analysis)
OPENAI_API_KEY=sk-proj-YOUR_KEY
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_ANALYSIS_MODEL=gpt-4o

# Anthropic (final polish)
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# ======================
# APPLICATION SETTINGS
# ======================
# FastAPI
APP_NAME=Unified Scraper
APP_VERSION=1.0.0
APP_ENV=development  # development, staging, production
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
SCRAPE_CONCURRENT_JOBS=5
EMBEDDING_BATCH_SIZE=100

# ======================
# MONITORING
# ======================
# Sentry (error tracking)
SENTRY_DSN=https://YOUR_KEY@sentry.io/YOUR_PROJECT

# Prometheus (metrics)
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# ======================
# DEPLOYMENT
# ======================
# Hetzner VPS (production)
HETZNER_HOST=YOUR_IP_ADDRESS
HETZNER_USER=root

# GitHub Actions
GITHUB_TOKEN=ghp_YOUR_TOKEN

# ======================
# FEATURE FLAGS
# ======================
ENABLE_TWITTER_SCRAPER=true
ENABLE_YOUTUBE_SCRAPER=true
ENABLE_REDDIT_SCRAPER=true
ENABLE_WEB_SCRAPER=true
ENABLE_AMAZON_SCRAPER=false  # Stretch goal
ENABLE_PATTERN_DETECTION=true
ENABLE_COURSE_GENERATION=true
```

---

## Final Approval Request

### Summary

This technical proposal outlines a comprehensive architecture for IAC-032 Unified Scraper:

1. **Containerized Deployment**: Podman on Hetzner VPS ($13/mo)
2. **7 Parallel Agents**: Specialized CCW teams for modular development
3. **5-Gate CI/CD Pipeline**: Automated quality assurance and deployment
4. **Cost-Optimized Stack**: $43-92/mo vs competitors $49-299/mo
5. **Production Timeline**: 6-7 hours parallel execution

### Requesting Approval For

1. **Architecture**: Containerized microservices with PostgreSQL + pgvector
2. **Agent Structure**: 7 specialized CCW agents (Alpha-Eta)
3. **Tech Stack**: FastAPI, ChromaDB, Redis+RQ, OpenAI embeddings
4. **Deployment Target**: Hetzner CX31 VPS
5. **CI/CD Pipeline**: GitHub Actions with 5 quality gates
6. **Budget**: $43-92/month operational costs

### Next Steps Upon Approval

1. **Spawn Agent Alpha** (Database Architect) - IMMEDIATE
2. **Prepare Agent Prompts** (Beta-Eta) - Ready to spawn after Alpha completes
3. **Configure GitHub Repository** - Secrets, workflows, branch protection
4. **Provision Hetzner VPS** - Initial server setup
5. **Execute 3-Day Sprint** - Phase 1 + 2 + 3 = MVP Complete

---

**Document Stats**:
- Total Lines: 2,100+
- Sections: 11 main + 3 appendices
- Mermaid Diagrams: 5
- Code Examples: 30+
- Risk Assessment: 10 critical points
- Cost Analysis: Complete ROI breakdown

**Awaiting Product Manager Approval**

---

*Last Updated: 2025-11-16*
*Project: IAC-032 Unified Scraper*
*Sprint: Day 1 of 3 (Architecture & Planning)*
*Next Milestone: Agent Alpha Spawn*
