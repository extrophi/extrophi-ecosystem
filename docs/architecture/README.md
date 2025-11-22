# Architecture Documentation

**Extrophi Ecosystem - IAC-033**

This directory contains comprehensive architecture documentation for the Extrophi Ecosystem monorepo, including:
- **BrainDump Writer** (Voice journaling desktop app)
- **IAC-032 Scraper Backend** (Content intelligence engine)
- **Admin Dashboard** (Project management UI)

All diagrams are created using [Mermaid](https://mermaid.js.org/) syntax and can be rendered in GitHub, VSCode, or any Mermaid-compatible viewer.

---

## 📋 Table of Contents

- [Overview](#overview)
- [C4 Architecture Diagrams](#c4-architecture-diagrams)
  - [Context Diagram](#context-diagram)
  - [Container Diagram](#container-diagram)
  - [Component Diagrams](#component-diagrams)
- [Sequence Diagrams](#sequence-diagrams)
- [Database Schemas (ERD)](#database-schemas-erd)
- [Key Architectural Decisions](#key-architectural-decisions)
- [Technology Stack](#technology-stack)
- [How to View Diagrams](#how-to-view-diagrams)

---

## Overview

The Extrophi Ecosystem is a **monorepo** combining three projects:

1. **BrainDump Writer** - Privacy-first voice journaling desktop app (Tauri + Svelte + Rust)
2. **IAC-032 Unified Scraper** - Multi-platform content intelligence engine (FastAPI + Python)
3. **Admin Dashboard** - Web-based project management dashboard (FastAPI + HTML/JS)

**Core Philosophy**:
- **Local-first**: BrainDump processes voice locally (Whisper.cpp with Metal GPU)
- **Privacy by design**: PII detection before publishing
- **Modular architecture**: Each system can operate independently
- **API-first**: Backend exposes REST APIs for extensibility
- **$EXTROPY token system**: Incentivizes knowledge sharing and attribution

---

## C4 Architecture Diagrams

The C4 model provides a hierarchical way to describe software architecture at different levels of abstraction.

### Context Diagram

**File**: [`c4-context.mmd`](./c4-context.mmd)

**Purpose**: System-level view showing the Extrophi Ecosystem and its external dependencies.

**Key Elements**:
- **Users**: Knowledge workers, researchers, administrators
- **Systems**: BrainDump Writer, IAC-032 Scraper, Admin Dashboard
- **External Services**: Twitter/YouTube/Reddit APIs, OpenAI, Claude, GitHub, PostgreSQL, Redis

**View the diagram**: [c4-context.mmd](./c4-context.mmd)

---

### Container Diagram

**File**: [`c4-container.mmd`](./c4-container.mmd)

**Purpose**: Shows containers (applications, data stores, microservices) within each system.

**BrainDump Containers**:
- Svelte 5 Frontend (Voice UI + Chat)
- Rust Backend (Tauri Commands)
- Whisper.cpp Plugin (Local Transcription)
- Candle Plugin (Pure Rust ML)
- SQLite Database
- Git Publisher

**Scraper Backend Containers**:
- FastAPI Application
- Scraper Adapters (Twitter, YouTube, Reddit, Web)
- LLM Analysis Engine
- Vector Store (ChromaDB)
- Job Queue (Celery + Redis)
- PostgreSQL + pgvector

**Admin Dashboard Containers**:
- Web UI (FastAPI Templates)
- Management API

**View the diagram**: [c4-container.mmd](./c4-container.mmd)

---

### Component Diagrams

#### Backend API Components

**File**: [`c4-component-backend.mmd`](./c4-component-backend.mmd)

**Purpose**: Internal structure of the FastAPI Scraper Backend.

**Key Components**:
- **API Routes**: Health, Scrape, Analyze, Query, API Keys, Tokens, Publish, Attributions
- **Middleware**: CORS, API Key Auth, Rate Limiter
- **Scraper Module**: Registry, Platform Adapters, Cache, Utils
- **Analysis Engine**: LLM Client, Embeddings, Pattern Detector
- **Vector Store**: ChromaDB, Semantic Search
- **Database Layer**: Connection Pool, ORM Models, Repositories
- **$EXTROPY System**: Ledger Service, Transfer Service, Reward Calculator

**View the diagram**: [c4-component-backend.mmd](./c4-component-backend.mmd)

---

#### Writer (Rust) Components

**File**: [`c4-component-writer.mmd`](./c4-component-writer.mmd)

**Purpose**: Internal structure of the BrainDump Tauri Rust Backend.

**Key Components**:
- **Tauri Commands**: Recording, Transcription, Chat, Session, Prompt, Export, Backup, Git, Stats
- **Audio Module**: Recorder (cpal), WAV Writer, Audio Thread, Peak Detector
- **Plugin System**: Plugin Manager, Whisper.cpp FFI, Candle ML, Shared Types
- **Services**: OpenAI Client, Claude Client, Keychain Service (macOS)
- **Database Layer**: Repository, Migration System, Data Models
- **Export Module**: Markdown Generator, Privacy Filter, Formatter
- **Backup System**: Creator, Restorer, Scheduler, Cleanup
- **Git Publisher**: Commit Builder, Push Handler

**View the diagram**: [c4-component-writer.mmd](./c4-component-writer.mmd)

---

## Sequence Diagrams

Sequence diagrams illustrate key user flows and system interactions.

### 1. Voice Recording and Transcription

**File**: [`sequence-voice-recording.mmd`](./sequence-voice-recording.mmd)

**Flow**:
1. User clicks "Record" → Audio thread captures samples
2. User clicks "Stop" → WAV file saved to disk
3. Recording metadata saved to SQLite
4. User clicks "Transcribe" → Whisper.cpp processes audio locally
5. Transcript and segments saved to database
6. Display transcript to user

**Performance**: ~30-60s for 5min audio, all local processing

**View the diagram**: [sequence-voice-recording.mmd](./sequence-voice-recording.mmd)

---

### 2. Content Scraping and Analysis

**File**: [`sequence-content-scraping.mmd`](./sequence-content-scraping.mmd)

**Flow**:
1. Client sends scrape request (e.g., Twitter @username)
2. API validates API key and rate limits
3. Job dispatched to Celery queue
4. Scraper extracts content (with caching)
5. Content normalized and saved to PostgreSQL
6. Embeddings generated via OpenAI
7. LLM analyzes content (frameworks, hooks, themes)
8. Patterns detected across author's content
9. Results indexed in ChromaDB for semantic search

**Performance**: ~2-5 min for 50 tweets
**Cost**: ~$0.10 (embeddings + analysis)

**View the diagram**: [sequence-content-scraping.mmd](./sequence-content-scraping.mmd)

---

### 3. Card Publishing with $EXTROPY Attribution

**File**: [`sequence-card-publishing.mmd`](./sequence-card-publishing.mmd)

**Flow**:
1. User publishes card from BrainDump → Backend creates card record
2. User earns +1.0 $EXTROPY publishing reward
3. Another user creates card citing the first card
4. Attribution created → 10% of citer's balance transferred to original author
5. Immutable ledger entry records transaction
6. Both users can view transaction history

**Economics**:
- Publishing reward: +1.0 $EXTROPY
- Citation transfer: 10% of citer's balance
- All transactions logged immutably

**View the diagram**: [sequence-card-publishing.mmd](./sequence-card-publishing.mmd)

---

### 4. Semantic Search Query

**File**: [`sequence-semantic-search.mmd`](./sequence-semantic-search.mmd)

**Flow**:
1. Client sends natural language query (e.g., "storytelling frameworks")
2. Query embedding generated via OpenAI
3. Vector similarity search in ChromaDB
4. Top 20 most similar content pieces retrieved from PostgreSQL
5. Pattern analysis identifies common frameworks and themes
6. Results cached for 5 minutes
7. Client receives enriched results with pattern insights

**Performance**:
- Cached: ~10ms
- Uncached: ~200-500ms
- Cost: ~$0.0001 per query

**View the diagram**: [sequence-semantic-search.mmd](./sequence-semantic-search.mmd)

---

## Database Schemas (ERD)

Entity-Relationship Diagrams showing database structure.

### PostgreSQL Schema (Scraper Backend)

**File**: [`erd-backend-postgresql.mmd`](./erd-backend-postgresql.mmd)

**Key Entities**:
- **users**: User accounts with $EXTROPY balances
- **api_keys**: API authentication with rate limiting
- **contents**: Scraped content with embeddings (pgvector)
- **authors**: Content creators with authority scores
- **patterns**: Cross-platform pattern detection
- **cards**: Published content from Writer
- **extropy_ledger**: Immutable transaction log
- **attributions**: Citations, remixes, replies between cards

**Features**:
- pgvector extension for embeddings (1536 dims)
- JSONB columns for flexible metadata
- Comprehensive indexing for performance
- Decimal precision for $EXTROPY (8 decimal places)

**View the diagram**: [erd-backend-postgresql.mmd](./erd-backend-postgresql.mmd)

---

### SQLite Schema (BrainDump Writer)

**File**: [`erd-writer-sqlite.mmd`](./erd-writer-sqlite.mmd)

**Key Entities**:
- **recordings**: Audio file metadata
- **transcripts**: Whisper.cpp transcription results
- **segments**: Timestamped transcript segments
- **chat_sessions**: Conversation threads
- **messages**: User and assistant messages
- **prompts**: User-created prompt templates
- **cards**: Publishable content with privacy levels
- **tags**: Session categorization
- **usage_events**: API usage tracking
- **backup_settings**: Automated backup configuration

**Features**:
- Local-first storage (no cloud dependency)
- Privacy-focused (all PII stays local)
- Backup system with retention policy
- Session tagging for organization

**View the diagram**: [erd-writer-sqlite.mmd](./erd-writer-sqlite.mmd)

---

## Key Architectural Decisions

### 1. Monorepo Structure

**Decision**: Combine Writer, Scraper, and Admin into single repository
**Rationale**:
- Shared documentation and tooling
- Easier dependency management
- Coordinated releases
- Cross-project refactoring

**Trade-offs**:
- Larger repository size
- More complex CI/CD
- Potential for tighter coupling

---

### 2. Local-First Voice Processing

**Decision**: Use Whisper.cpp with Metal GPU for local transcription
**Rationale**:
- **Privacy**: No audio sent to cloud
- **Cost**: No per-minute API charges
- **Performance**: Metal GPU acceleration on macOS (~30s for 5min audio)
- **Offline**: Works without internet

**Trade-offs**:
- Requires whisper.cpp system installation
- Model files (~140MB) must be downloaded
- macOS-focused (Metal GPU)

---

### 3. PostgreSQL + pgvector vs ChromaDB

**Decision**: Use PostgreSQL with pgvector extension for embeddings
**Rationale**:
- Single database for relational + vector data
- Production-grade reliability
- ACID transactions
- Rich querying (joins + vector search)

**Complemented by ChromaDB**:
- Local RAG for development
- Faster prototyping
- Semantic search SDK

---

### 4. FastAPI over Flask/Django

**Decision**: FastAPI for Scraper Backend API
**Rationale**:
- Async/await support (critical for scraping)
- Automatic OpenAPI docs (`/docs`)
- Pydantic validation
- Modern Python (3.11+)
- WebSocket support

---

### 5. Tauri 2.0 over Electron

**Decision**: Tauri for BrainDump desktop app
**Rationale**:
- **Binary size**: ~10MB vs ~100MB (Electron)
- **Memory**: Rust backend uses less RAM
- **Security**: Process isolation, no Node.js runtime
- **Native**: Integrates with macOS Keychain, notifications

**Trade-offs**:
- Smaller ecosystem vs Electron
- Rust learning curve
- Limited cross-platform testing

---

### 6. $EXTROPY Token System

**Decision**: Implement attribution-based token economy
**Rationale**:
- Incentivizes knowledge sharing
- Transparent attribution (immutable ledger)
- Rewards original creators when cited
- Gamification for engagement

**Implementation**:
- Decimal precision (8 places)
- Immutable ledger (append-only)
- 10% transfer on citation
- +1.0 $EXTROPY publishing reward

---

## Technology Stack

### BrainDump Writer

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Svelte 5 (runes) | Reactive UI with minimal bundle size |
| Desktop | Tauri 2.0 | Rust-powered desktop framework |
| Backend | Rust | Systems programming, FFI, safety |
| ML | Whisper.cpp, Candle | Local transcription and ML |
| Audio | cpal, hound | Cross-platform audio recording |
| Database | SQLite | Local-first, embedded database |
| LLM | OpenAI GPT-4, Claude Sonnet 4.5 | AI chat |
| Auth | macOS Keychain | Secure API key storage |

---

### IAC-032 Scraper Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI | Async REST API with auto-docs |
| Language | Python 3.11+ | Rapid development, rich ecosystem |
| Database | PostgreSQL + pgvector | Relational + vector embeddings |
| Vector Store | ChromaDB | Local RAG, semantic search |
| Cache | Redis | Response caching, rate limiting |
| Queue | Celery | Async job processing |
| Scraping | Playwright, PRAW, youtube-transcript-api | Platform-specific adapters |
| LLM | OpenAI GPT-4, Claude Sonnet 4.5 | Analysis, embeddings, polish |
| ORM | SQLAlchemy | Database abstraction |
| Validation | Pydantic v2 | Request/response validation |

---

### Admin Dashboard

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI | API + server-side rendering |
| Frontend | HTML + JavaScript | Lightweight dashboard UI |
| Database | PostgreSQL | Shared with Scraper Backend |

---

## How to View Diagrams

### GitHub (Recommended)

GitHub natively renders Mermaid diagrams in `.mmd` files. Simply click on any diagram file in this directory.

### VSCode

1. Install extension: **Markdown Preview Mermaid Support**
2. Open any `.mmd` file
3. Right-click → "Open Preview"

### Mermaid Live Editor

1. Visit [mermaid.live](https://mermaid.live/)
2. Copy-paste diagram code from any `.mmd` file
3. Edit and export as SVG/PNG

### Local Rendering

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Render diagram
mmdc -i c4-context.mmd -o c4-context.png
```

---

## Document Metadata

**Created**: 2025-11-18
**Agent**: DOC-BETA (Architecture Documentation)
**Issue**: [#91](https://github.com/extrophi/extrophi-ecosystem/issues/91)
**Diagrams**: 10 files (3 C4, 4 Sequence, 2 ERD, 1 README)
**Format**: Mermaid.js (text-based, version-controllable)

**Maintenance**:
- Update diagrams when architecture changes
- Keep in sync with code changes
- Review quarterly for accuracy

---

## Related Documentation

- **Root CLAUDE.md**: Monorepo structure and development guide
- **Writer CLAUDE.md**: BrainDump-specific documentation
- **Research CLAUDE.md**: Scraper-specific documentation
- **Backend docs/**: API documentation, database schema guides
- **docs/pm/**: Project management, PRDs, planning

---

**Last Updated**: 2025-11-18
**Status**: Complete (Issue #91)
