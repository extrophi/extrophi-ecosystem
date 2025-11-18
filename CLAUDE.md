# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Repository Overview

**IAC-033 Extrophi Ecosystem** is a **monorepo** containing three merged projects:

1. **BrainDump v3.0** (`writer/`, root) - Privacy-first voice journaling desktop app
2. **IAC-032 Unified Scraper** (`research/`, `backend/`) - Multi-platform content intelligence engine
3. **Admin Tools** (`admin/`, `tools/`) - Project dashboard and utilities

**Branch**: `main` (merged from multiple project branches)

---

## Project Structure

```
IAC-033-extrophi-ecosystem/
├── writer/                    # BrainDump v3.0 (Tauri + Svelte)
│   ├── src/                   # Svelte 5 frontend
│   ├── src-tauri/             # Rust backend
│   ├── package.json           # Node dependencies
│   └── CLAUDE.md              # BrainDump-specific guide
│
├── research/                  # IAC-032 research workspace
│   ├── backend/               # FastAPI scraper implementation
│   ├── docs/                  # Architecture & planning docs
│   ├── tools/                 # Doc scraper utilities
│   └── CLAUDE.md              # Scraper-specific guide
│
├── backend/                   # Shared backend (IAC-011 sovereign backend)
│   ├── api/                   # FastAPI routes
│   ├── scrapers/              # Platform adapters
│   ├── db/                    # Database layer
│   └── pyproject.toml         # Python dependencies (UV)
│
├── admin/                     # Project dashboard (FastAPI web UI)
│   └── package.json
│
├── tools/                     # Shared utilities
│   ├── doc-scraper/           # Documentation scraper
│   └── yt-agent-app/          # YouTube agent tool
│
├── src/                       # Root Svelte source (shared)
├── src-tauri/                 # Root Tauri source (shared)
├── docs/                      # Shared documentation
├── tests/                     # Shared test suite
└── scripts/                   # Automation scripts
```

---

## Quick Start by Project

### BrainDump v3.0 (Voice Journaling)

**Location**: `writer/` subdirectory

**Development**:
```bash
cd writer
npm install
npm run tauri:dev  # Launches Tauri app with hot reload
```

**Build**:
```bash
npm run tauri:build  # Creates .app/.dmg
```

**Tech Stack**: Tauri 2.0, Svelte 5 (runes), Rust, whisper.cpp, SQLite

**Key Features**: Local voice transcription, AI chat (OpenAI/Claude), privacy-first design

**Documentation**: `writer/CLAUDE.md`, `docs/dev/PROJECT_STATUS_2025-11-16.md`

---

### IAC-032 Unified Scraper (Content Intelligence)

**Location**: `research/` and `backend/` subdirectories

**Development**:
```bash
# Setup Python environment (use UV per parent CLAUDE.md)
cd research/backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run API server
uvicorn main:app --reload
```

**Tech Stack**: FastAPI, PostgreSQL + pgvector, ChromaDB, Redis, Playwright, OpenAI

**Key Features**: Multi-platform scraping (Twitter/YouTube/Reddit), RAG semantic search, LLM analysis

**Documentation**: `research/CLAUDE.md`, `research/ORCHESTRATION.md`

---

### Admin Dashboard

**Location**: `admin/` subdirectory

**Development**:
```bash
cd admin
npm install
npm run dev
```

**Purpose**: Web-based project management dashboard

---

## Development Standards (Applies to All Projects)

### Python Package Management

**ALWAYS use UV** (not pip, not homebrew):
```bash
# Create virtual environment
uv venv

# Activate
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install packages
uv pip install <package>
```

**Location**: Each Python project has its own `pyproject.toml`:
- `backend/pyproject.toml` - Shared backend dependencies
- `research/backend/pyproject.toml` - Scraper-specific deps
- `tools/doc-scraper/pyproject.toml` - Doc scraper deps

### Node.js Version Management

**ALWAYS use NVM** (not homebrew):
```bash
nvm use 18  # or version specified in .nvmrc
npm install
```

### Testing

**Python**:
```bash
# Run from project root
pytest

# With coverage
pytest --cov=backend --cov-report=term-missing
```

**Rust**:
```bash
cd src-tauri
cargo test
```

**Frontend** (Svelte):
```bash
npm test           # Run tests
npm run test:watch # Watch mode
```

---

## Common Commands by Use Case

### Working on BrainDump Features

```bash
cd writer

# Development
npm run tauri:dev

# Build for production
npm run tauri:build

# Run Rust tests only
cd src-tauri && cargo test

# Lint frontend
npm run lint

# Type check Svelte
npm run check
```

### Working on Scraper Backend

```bash
cd research/backend

# Setup (first time)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run API server
uvicorn main:app --reload --port 8000

# Run tests
pytest

# Database migrations (if using Alembic)
alembic upgrade head
```

### Documentation Scraping

```bash
cd tools/doc-scraper

# Setup
uv venv
source .venv/bin/activate
uv pip install beautifulsoup4 markitdown requests

# Run scraper
python scrape_docs.py

# Output: docs/dev/{platform}/
```

### Bootstrap Project Dashboard

```bash
# Run bootstrap script (production deployment)
sudo ./bootstrap.sh

# Or manual setup (development)
cd admin
npm install
npm run dev
```

---

## Architecture Patterns

### Monorepo Structure

Each subproject (`writer/`, `research/`, `admin/`) is **semi-independent**:
- Has its own `CLAUDE.md` for project-specific context
- Has its own dependencies (`package.json`, `pyproject.toml`)
- Can be developed in isolation
- Shares common utilities via `tools/` and `scripts/`

### Shared Backend (`backend/`)

The `backend/` directory contains **IAC-011 sovereign backend** - a shared FastAPI foundation used by multiple projects:

**Key Modules**:
- `api/` - REST endpoints
- `scrapers/` - Platform adapters (Twitter, YouTube, Reddit)
- `db/` - Database layer (PostgreSQL + pgvector)
- `queue/` - Async job processing (Redis + Celery)
- `vector/` - ChromaDB RAG integration
- `analysis/` - LLM analysis pipeline

**Dependencies**: See `backend/pyproject.toml`

### Documentation Structure

**Project-Specific Documentation** (Each module has its own `docs/` directory):
- `writer/docs/` - BrainDump documentation (45 dev docs, 29 research docs, 11 agent logs)
  - `writer/CLAUDE.md` - Module-specific guidance
  - `writer/docs/pm/` - Writer project management
  - `writer/docs/dev/` - Svelte, Tauri, Rust guides
  - `writer/docs/research/` - Feature research (accessibility, security, UX)
  - `writer/docs/agents/` - Agent work logs

- `research/docs/` - IAC-032 Scraper documentation (22 PM docs, research artifacts)
  - `research/CLAUDE.md` - Module-specific guidance
  - `research/ORCHESTRATION.md` - Team execution guide
  - `research/docs/pm/` - PRDs, architecture, planning
  - `research/docs/research/` - Dan Koe analysis, platform comparisons
  - `research/docs/agents/` - Agent task prompts

- `backend/docs/` - IAC-011 Backend documentation (newly created)
  - `backend/docs/pm/` - Backend planning
  - `backend/docs/dev/` - API, database, deployment guides

**Monorepo-Level Documentation** (Root `docs/` directory):
- `docs/pm/` - **Coordination hub** with module subdirectories:
  - Root: MASTER-EXECUTION-PLAN, ROOT-CCL-INSTRUCTIONS, architecture
  - `docs/pm/writer/` - Writer CCL instructions and proposals
  - `docs/pm/research/` - Research CCL instructions and proposals
  - `docs/pm/backend/` - Backend CCL instructions and proposals
  - `docs/pm/orchestrator/` - Orchestrator CCL instructions and proposals

- `docs/dev/` - Monorepo-wide development guides - **FRESH**
- `docs/research/` - Cross-project research - **FRESH**
- `docs/agents/` - Monorepo-level agent logs - **FRESH**
- `docs/archive/2025-11-18_021849/` - **ARCHIVED** historical documentation

**Archive Contents** (`docs/archive/2025-11-18_021849/`):
- Previous agent reports and work logs
- Historical development documentation
- Old research documentation
- Root-level report files (PR summaries, test reports, etc.)
- CI/CD setup documentation
- Legacy templates and architecture docs

---

## Key Technologies

### BrainDump Tech Stack

**Frontend**: Svelte 5 with runes (new reactive syntax)
```javascript
// ✅ Svelte 5 runes (REQUIRED)
let { myProp = $bindable() } = $props();
let computed = $derived(myProp * 2);

// ❌ Svelte 4 syntax (DO NOT USE)
export let myProp;
$: computed = myProp * 2;
```

**Backend**: Rust + Tauri 2.0
- FFI integration with whisper.cpp for local transcription
- SQLite with Repository pattern
- macOS Keychain for API key storage

**Critical Files**:
- `src-tauri/src/plugin/whisper_cpp.rs` - Whisper FFI bindings
- `src-tauri/build.rs` - Build configuration (pkg-config for whisper.cpp)
- `src-tauri/src/db/repository.rs` - Database abstraction

### Scraper Tech Stack

**Backend**: FastAPI + Python 3.11+
- PostgreSQL with pgvector extension for embeddings
- ChromaDB for local RAG
- Redis + Celery for job queues

**Scraping**:
- Playwright (Twitter OAuth, dynamic content)
- youtube-transcript-api (YouTube transcripts)
- PRAW (Reddit API)
- Jina.ai Reader API (50K pages/month FREE)
- ScraperAPI (fallback for complex sites)

**LLM Analysis**:
- OpenAI GPT-4 (bulk processing)
- Claude Sonnet 4.5 (copywriting polish)

---

## Common Gotchas

### 1. Svelte 5 Runes Are Required

Files in `src/`, `writer/src/` use **Svelte 5 runes syntax** exclusively.

**Migration Required**:
- `export let prop` → `let { prop } = $props()`
- `$: derived = ...` → `let derived = $derived(...)`
- Two-way binding: `let { prop = $bindable() } = $props()`

**Affected Files**:
- `src/App.svelte`
- `src/components/ChatPanel.svelte`
- `src/components/SettingsPanel.svelte`
- All components in `writer/src/components/`

### 2. Python: ALWAYS Use UV

**Correct**:
```bash
uv venv
source .venv/bin/activate
uv pip install fastapi
```

**Incorrect** (will cause version conflicts):
```bash
python -m venv .venv
pip install fastapi
```

### 3. Whisper.cpp Must Be Installed

BrainDump requires whisper.cpp with Metal GPU support:

```bash
# macOS (required for development)
brew install whisper-cpp

# Download model (141MB)
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

**Build will fail** if whisper.cpp is not found via pkg-config.

### 4. Merge Conflicts in Root Files

The root `README.md` and `CLAUDE.md` had merge conflicts from combining projects. This file (CLAUDE.md) resolves those conflicts by documenting the **monorepo structure** as the source of truth.

### 5. Environment Variables

Each project needs its own `.env` file:

**BrainDump** (`writer/.env`):
```bash
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
```

**Scraper** (`research/.env`):
```bash
OPENAI_API_KEY=sk-...
SCRAPER_API_KEY=...
JINA_API_KEY=...  # Free tier, no key required
```

**Never commit** `.env` files (in `.gitignore`).

---

## Git Workflow

### Branch Structure

- `main` - Stable monorepo with all projects merged
- `writer/*` - BrainDump feature branches
- `research/*` - Scraper feature branches
- `iac032/*` - Legacy scraper branches (merged)

### Commit Message Format

```bash
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
**Scopes**: `writer`, `research`, `backend`, `admin`, `tools`, `docs`

**Examples**:
```bash
# BrainDump feature
feat(writer): Add Whisper model selection UI

# Scraper improvement
feat(research): Port IAC-024 Twitter OAuth scraper

# Documentation
docs(backend): Add database schema documentation

# Cross-project fix
fix(backend): Resolve PostgreSQL connection pooling issue
```

---

## Testing Strategy

### BrainDump Tests

**Rust** (`src-tauri/src/`):
```bash
cd src-tauri
cargo test                    # All tests
cargo test --test integration # Integration tests only
```

**Svelte** (`src/`, `writer/src/`):
```bash
npm test           # Vitest
npm run test:ui    # Visual test runner
```

**Current Coverage**: ~5% (baseline unit tests)
**Goal**: 60%+ before v1.0

### Scraper Tests

**Backend** (`research/backend/`, `backend/`):
```bash
pytest                                    # All tests
pytest tests/test_scrapers.py             # Scraper tests only
pytest --cov=backend --cov-report=html    # Coverage report
```

**Current Coverage**: ~30% (scraper adapters tested)
**Goal**: 80%+ for production

---

## Debugging

### BrainDump (Tauri App)

**Rust Logs**:
```bash
npm run tauri:dev  # Stdout shows Rust logs
```

**Frontend Console**:
- Press `Cmd+Option+I` in running app
- View Svelte component state, Tauri command responses

**Common Errors**:
- "library 'whisper' not found" → Install whisper.cpp via Homebrew
- "Cannot use `export let` in runes mode" → Migrate to Svelte 5 runes
- "API key not found" → Create `.env` file or add via Settings UI

### Scraper Backend

**API Logs**:
```bash
uvicorn main:app --reload --log-level debug
```

**Database Queries**:
```bash
# Connect to PostgreSQL
psql -d unified_scraper

# View recent scrapes
SELECT platform, COUNT(*) FROM contents GROUP BY platform;
```

**Common Errors**:
- Import errors → Ensure `uv venv` is activated
- Connection refused → Check PostgreSQL is running (`brew services start postgresql@16`)
- Playwright timeout → Increase timeout, check anti-bot measures

---

## Production Deployment

### BrainDump (Desktop App)

```bash
cd writer
npm run tauri:build

# Output: src-tauri/target/release/bundle/
# macOS: .app, .dmg
# Windows: .exe, .msi
# Linux: .AppImage, .deb
```

**Distribution**: GitHub Releases, direct download

### Scraper Backend (Server)

**Option 1: Podman Compose** (recommended):
```bash
# See podman-compose.yml
podman-compose up -d
```

**Option 2: Manual Deployment**:
```bash
# Bootstrap script handles Nginx, PostgreSQL, Redis
sudo ./bootstrap.sh
```

**Option 3: Cloud (Hetzner VPS)**:
- See `research/docs/pm/` for deployment guides
- Uses Docker/Podman containers
- Nginx reverse proxy
- PostgreSQL + pgvector

---

## External Dependencies

### Required System Packages

**macOS**:
```bash
brew install whisper-cpp portaudio postgresql@16 pgvector redis
```

**Linux (Ubuntu/Debian)**:
```bash
apt install build-essential pkg-config libssl-dev postgresql postgresql-contrib redis-server
```

### Required API Keys

**BrainDump**:
- OpenAI API key (for GPT-4 chat)
- Claude API key (for Claude Sonnet chat)

**Scraper**:
- OpenAI API key (embeddings + bulk analysis)
- ScraperAPI key (optional, fallback scraping)
- Jina.ai (no key required for free tier)

**Configuration**: Via `.env` files (see "Environment Variables" above)

---

## Related Projects

### IAC-024 Tweet Hunter
**Location**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/`
**Purpose**: Production Twitter scraper with OAuth
**Reusable Code**:
- `src/scrapers/persistent_x_session.py` (1,231 lines)
- `src/scrapers/playwright_oauth_client.py` (534 lines)

**Integration**: Port to `backend/scrapers/adapters/twitter.py`

### IAC-011 Sovereign Backend
**Location**: `backend/` (merged into this monorepo)
**Purpose**: Shared FastAPI foundation for all projects

---

## Documentation Quick Reference

**BrainDump**:
- `writer/CLAUDE.md` - Project guide
- `docs/archive/2025-11-18_021849/dev/PROJECT_STATUS_2025-11-16.md` - Feature matrix (archived)
- `docs/archive/2025-11-18_021849/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md` - 14 open issues (archived)

**Scraper**:
- `research/CLAUDE.md` - Project guide
- `research/ORCHESTRATION.md` - Team workflow
- `docs/pm/PRD_PROPER.md` - Product requirements (source of truth)

**Development** (archived to `docs/archive/2025-11-18_021849/`):
- `dev/svelte/` - Svelte 5 runes documentation
- `dev/tauri/` - Tauri 2.0 guides
- `dev/rust-ffi/` - FFI patterns

**Current Documentation**:
- `docs/README.md` - Documentation index and structure
- `docs/pm/` - Active project management docs
- `docs/dev/README.md` - Guidelines for new development docs
- `docs/research/README.md` - Research documentation standards
- `docs/agents/README.md` - Agent task logging guidelines

---

## Success Criteria

### BrainDump v1.0
- [ ] Voice recording + transcription working
- [ ] AI chat with provider selection (OpenAI/Claude)
- [ ] Privacy scanner with PII detection
- [ ] Session management (create/delete/rename)
- [ ] Prompt templates (CRUD UI)
- [ ] Settings persistence to database
- [ ] Export transcripts to markdown
- [ ] macOS .app distribution

**Current Status**: 60% complete, 14 features missing

### Scraper MVP (Day 3)
- [ ] Twitter scraper (100 tweets → PostgreSQL)
- [ ] YouTube scraper (transcripts + metadata)
- [ ] Reddit scraper (50 posts)
- [ ] RAG semantic search
- [ ] Pattern detection (cross-platform elaboration)
- [ ] Course script generator
- [ ] Export to markdown

**Current Status**: Day 1 research complete, implementation in progress

---

## Documentation Archive Note

**Archive Date**: 2025-11-18 02:18:49
**Archive Location**: `docs/archive/2025-11-18_021849/`

All historical documentation has been archived to prepare for new documentation. The `docs/pm/` directory contains current project management documents. All other documentation directories (`dev/`, `research/`, `agents/`) have been reset with fresh README files to guide future documentation.

To access archived documentation, see the archive directory structure:
```bash
docs/archive/2025-11-18_021849/
├── agents/           # Historical agent work logs
├── dev/              # Previous development docs
├── research/         # Old research findings
├── ci-setup/         # CI/CD configuration docs
├── templates/        # Legacy templates
├── ARCHITECTURE.md   # Archived architecture docs
├── backend-review.md
├── KEYBOARD_SHORTCUTS_QUICK_REFERENCE.md
└── TASKS.md
```

---

**Last Updated**: 2025-11-18
**Monorepo**: IAC-033 Extrophi Ecosystem
**Projects**: BrainDump v3.0, IAC-032 Unified Scraper, Admin Tools
**Branch**: main
**Documentation Status**: Cleaned and archived - ready for new docs
