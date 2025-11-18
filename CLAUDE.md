# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

<<<<<<< HEAD
**BrainDump v3.0** - Privacy-first voice journaling desktop application
**Stack**: Tauri 2.0 + Svelte 5 + Rust + whisper.cpp FFI
**Status**: 60% feature-complete, buildable and runnable
**Current Branch**: `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`

---

## Essential Commands

### Development
```bash
# Start full development server (Tauri + Svelte with hot reload)
npm run tauri:dev

# Frontend only (Svelte dev server)
npm run dev
```

### Build
```bash
# Build production app (creates .app/.dmg)
npm run tauri:build

# Build frontend only
npm run build
```

### Testing
```bash
# Run Rust unit tests
cd src-tauri && cargo test

# Frontend tests (not yet configured)
npm test
```

### First-Time Setup
```bash
# 1. Install whisper.cpp (macOS)
brew install whisper-cpp

# 2. Install dependencies
npm install
cd src-tauri && cargo build

# 3. Download Whisper model (141MB)
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# 4. Create .env file with API keys
echo 'OPENAI_API_KEY=sk-...' > .env
echo 'CLAUDE_API_KEY=sk-ant-...' >> .env

# 5. Run development server
npm run tauri:dev
=======
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
>>>>>>> iac032/main
```

---

<<<<<<< HEAD
## Architecture Overview

### Stack Diagram
```
┌─────────────────────────────────────────────────┐
│         TAURI 2.0 DESKTOP APPLICATION           │
├─────────────────────────────────────────────────┤
│  Frontend: Svelte 5 (Runes API)                │
│  └─ Components: ChatPanel, SettingsPanel,       │
│     PrivacyPanel, TemplateSelector              │
├─────────────────────────────────────────────────┤
│  Backend: Rust                                  │
│  ├─ Audio: cpal + hound (recording)             │
│  ├─ Transcription: whisper.cpp FFI (Metal GPU)  │
│  ├─ Database: SQLite + Repository pattern       │
│  ├─ AI APIs: Claude + OpenAI HTTP clients       │
│  └─ Security: macOS Keychain (API keys)         │
└─────────────────────────────────────────────────┘
```

### Data Flow: Recording → Transcription → Chat

1. **User Records Audio**
   ```
   Click Record
   ├─> Tauri command: start_recording()
   ├─> Audio thread: cpal captures mic input
   └─> Real-time peak level visualization
   ```

2. **User Stops Recording**
   ```
   Click Stop
   ├─> Tauri command: stop_recording()
   ├─> Returns: f32 audio samples + sample_rate
   ├─> Resample to 16kHz (Whisper requirement)
   ├─> Save WAV to test-recordings/ (dev mode)
   ├─> Whisper.cpp FFI: transcribe via Metal GPU
   ├─> Auto-create chat session
   ├─> Save transcript as first user message
   └─> Return: transcript + session_id
   ```

3. **AI Chat Response**
   ```
   User sends message
   ├─> Check provider selection (OpenAI/Claude)
   ├─> ⚠️ BUG: Always routes to Claude API
   │   (Should route based on selected provider)
   ├─> API client sends HTTP request
   ├─> Save AI response as assistant message
   └─> Update chat UI
   ```

---

## Critical Documentation

⭐ **READ THESE FIRST** before making changes:

### Project Status & Missing Features
- **`docs/dev/PROJECT_STATUS_2025-11-16.md`**
  - Current state: what works vs what's broken
  - Feature completion matrix (60% complete)
  - 14 missing features before v1.0
  - Known bugs and issues

### Implementation Guide
- **`docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`**
  - 14 detailed GitHub issues with implementation steps
  - Priority breakdown (P1-P4)
  - Effort estimates (166 hours total)
  - Code file references for each issue

### Development Workflow
- **`docs/dev/HANDOFF_TO_WEB_TEAM.md`**
  - Complete development setup
  - Testing requirements
  - Code style conventions
  - Git workflow and PR process

### Agent Work Logs
- **`docs/agents/`** - 3 agent deliverable reports from overnight sprint

### Planning Archive
- **`docs/pm/archive/`** - Historical planning documents and proposals

---

## Key Architecture Patterns

### 1. Whisper.cpp FFI Integration

**Pattern**: Direct C FFI to whisper.cpp library (not subprocess).

```rust
// src-tauri/src/plugin/whisper_cpp.rs
extern "C" {
    fn whisper_init_from_file(path: *const c_char) -> *mut WhisperContext;
    fn whisper_full(ctx: *mut WhisperContext, ...);
}
```

**Build System** (`src-tauri/build.rs`):
- Uses `pkg-config` to find whisper.cpp installation
- Portable across systems (no hardcoded paths)
- Fallback with helpful error messages
- Feature flag: `[features] whisper = []`

**Model Path Logic**:
```rust
// Development: ./models/ggml-base.bin
// Production: Contents/Resources/models/ggml-base.bin
```

### 2. .env Auto-Import to Keychain

**Unique Pattern**: On app startup, API keys from `.env` are automatically imported to macOS Keychain.

```rust
// src-tauri/src/main.rs:12-42
fn main() {
    dotenv::dotenv().ok();  // Load .env file
    import_env_keys_to_keychain();  // Auto-import to keychain
    // ... rest of initialization
}
```

**Why**: Improves fresh install UX - users don't need to manually enter keys in Settings.

### 3. Auto-Session Creation

**Pattern**: Recording completion automatically creates a chat session with transcript as first message.

```rust
// src-tauri/src/commands.rs:212-252
// After transcription completes:
let session = ChatSession {
    title: Some(format!("Brain Dump {}", now.format("%Y-%m-%d %H:%M"))),
    ...
};
let session_id = db.create_chat_session(&session)?;
```

### 4. Repository Pattern (Database)

**Pattern**: All database operations go through `Repository` struct.

```rust
// src-tauri/src/db/repository.rs
pub struct Repository {
    conn: Arc<Mutex<Connection>>,
}

impl Repository {
    pub fn create_chat_session(&self, session: &ChatSession) -> Result<i64>
    pub fn get_messages(&self, session_id: i64) -> Result<Vec<Message>>
    // ... all CRUD operations
}
```

**Schema Location**: `src-tauri/src/db/schema.sql` (V2 migration applied)

### 5. Privacy Scanner (Client-Side)

**Pattern**: Regex-based PII detection before sending to AI.

```javascript
// src/lib/privacy_scanner.js
const PATTERNS = [
    { regex: /\b\d{3}-\d{2}-\d{4}\b/g, type: 'ssn', severity: 'danger' },
    { regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, type: 'email' },
    // ... more patterns
];

export function scanText(text) {
    // Returns: [{ type, value, severity }]
}
```

**Non-Blocking**: User can proceed even with detected PII.

---

## Critical Gotchas

### 1. Svelte 5 Runes (Breaking Change)

**MUST USE** new Svelte 5 syntax:

```javascript
// ❌ OLD (Svelte 4) - DO NOT USE
export let myProp;
$: derivedValue = myProp * 2;

// ✅ NEW (Svelte 5) - REQUIRED
let { myProp = $bindable() } = $props();
let derivedValue = $derived(myProp * 2);
```

**Files Using Runes**:
- `src/App.svelte` - Main state management
- `src/components/ChatPanel.svelte` - Two-way binding with `$bindable()`
- `src/components/SettingsPanel.svelte` - Provider selection state
- `src/components/PrivacyPanel.svelte` - Reactive PII scanning

### 2. Provider Selection Bug (P1 Critical)

**Bug**: User can select OpenAI or Claude in Settings, but chat **always uses Claude**.

**Location**: `src/components/ChatPanel.svelte:38`

```javascript
// ❌ BUG: Hardcoded to Claude
const response = await invoke('send_message_to_claude', { message: userMessage });

// ✅ FIX: Route based on provider
const command = selectedProvider === 'openai'
    ? 'send_openai_message'
    : 'send_message_to_claude';
const response = await invoke(command, { message: userMessage });
```

**Also Missing**: Provider selection is NOT persisted to database (resets on app restart).

### 3. Database Location Issue

**Current**: `~/.braindump/data/braindump.db`
**Should Be**: `~/Library/Application Support/com.braindump.app/braindump.db` (macOS standard)

### 4. Documentation is NOT in Git

**Critical**: `docs/` directory is in `.gitignore` - documentation won't be committed!

This is intentional (IP protection), but means:
- Documentation only exists locally
- Future contributors won't see it in GitHub
- Keep local copies safe

### 5. Test Data Accumulation

**Directories** (both in `.gitignore`):
- `test-recordings/` - WAV files from manual testing
- `test-transcripts/` - Markdown transcripts

**Privacy**: These contain user voice recordings - must NOT be committed to git.

---

## Database Schema (V2)

```sql
-- Core Tables
recordings          -- Audio file metadata (path, duration, sample_rate)
├─> transcripts     -- Whisper output (text, language, confidence)
    └─> segments    -- Future: Timestamp-aligned segments

chat_sessions       -- Conversation threads
├─> messages        -- User + AI messages
    └─> recording_id (nullable FK)

-- Configuration
prompt_templates    -- RAG prompts (brain_dump, end_of_day, crisis_support)
metadata            -- Schema version, app settings
```

**Migration**: V1 → V2 adds `chat_sessions` and `messages` tables.

---

## Common Development Tasks

### Adding a New Tauri Command

1. **Define command in `src-tauri/src/commands.rs`**:
```rust
#[tauri::command]
pub async fn my_new_command(
    param: String,
    state: tauri::State<'_, AppState>
) -> Result<String, String> {
    // Implementation
    Ok("result".to_string())
}
```

2. **Register in `src-tauri/src/main.rs`**:
```rust
.invoke_handler(tauri::generate_handler![
    // ... existing commands
    commands::my_new_command,
])
```

3. **Call from frontend**:
```javascript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke('my_new_command', { param: 'value' });
```

### Adding a Database Table

1. **Update schema**: `src-tauri/src/db/schema.sql`
2. **Create Rust model**: `src-tauri/src/db/models.rs`
3. **Add Repository methods**: `src-tauri/src/db/repository.rs`
4. **Increment schema version** in metadata table
5. **Test migration** from previous version

### Creating a New Svelte Component

1. **Create file**: `src/components/MyComponent.svelte`
2. **Use Svelte 5 runes**:
```svelte
<script>
    let { propName = $bindable('default') } = $props();
    let computed = $derived(propName.toUpperCase());
</script>

<div>{computed}</div>
```

3. **Import in parent**:
```svelte
<script>
    import MyComponent from './components/MyComponent.svelte';
</script>

<MyComponent bind:propName={myState} />
=======
## Hybrid Scraping Stack (UPDATED: Day 1 Research Complete)

**Research Completed**: 76 files, 20,946 lines in 45 minutes (7 parallel agents)

### Platform Decision: Hybrid FREE + Paid

**Primary (FREE Tier)**:
- **Jina.ai Reader API**: 50,000 pages/month FREE (static content)
  - Blogs, documentation, articles
  - Clean markdown conversion
  - No credit card required
  - Cost: $0/month

**Fallback (Paid)**:
- **ScraperAPI**: $49/mo, 100K credits (complex sites only)
  - JS-rendered pages (Twitter, Amazon)
  - Anti-bot protection needed
  - Structured data endpoints
  - Cost: $49/month (only if FREE tier exhausted)

**Platform APIs (FREE)**:
- Twitter: IAC-024 Playwright (no API costs)
- YouTube: youtube-transcript-api (no costs)
- Reddit: PRAW (1,000 req/10min, FREE)

**Total MVP Cost**: $0-89/month (vs competitors $49-299/mo)

### Cost Structure Breakdown

**Jina.ai (FREE)**:
- 50K pages/month = $0
- Static content (80% of use cases)
- markdown conversion built-in

**ScraperAPI (Fallback)**:
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
>>>>>>> iac032/main
```

---

<<<<<<< HEAD
## Known Issues (See docs/ for Full List)

### P1 Critical (Blocks v1.0)
1. **Provider selection NOT persisted** - Resets to "openai" on app restart
2. **Provider selection NOT connected to backend** - Always uses Claude API
3. **Prompt management UI missing** - Can SELECT but not CREATE/EDIT/DELETE
4. **Session management incomplete** - Can't delete or rename sessions

### P2 High
5. **No Whisper model selection** - Stuck with base model
6. **Search box non-functional** - UI exists but does nothing
7. **No audio playback** - Can't replay original recordings

**See**: `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md` for all 14 issues with implementation details.

---

## File Reference Map

### When Adding Features

**Audio Recording**:
- Commands: `src-tauri/src/commands.rs:14-82`
- Audio Module: `src-tauri/src/audio/mod.rs`
- UI: `src/App.svelte` (record button)

**Transcription**:
- Whisper FFI: `src-tauri/src/plugin/whisper_cpp.rs`
- Command: `src-tauri/src/commands.rs:168-252`

**Chat/AI**:
- Claude Client: `src-tauri/src/services/claude_api.rs`
- OpenAI Client: `src-tauri/src/services/openai_api.rs`
- UI: `src/components/ChatPanel.svelte`
- Commands: `src-tauri/src/commands.rs:254-406`

**Database**:
- Schema: `src-tauri/src/db/schema.sql`
- Models: `src-tauri/src/db/models.rs`
- Repository: `src-tauri/src/db/repository.rs`

**Settings**:
- UI: `src/components/SettingsPanel.svelte`
- Keychain: Uses `keyring` crate
- Commands: `src-tauri/src/commands.rs:408-526`

---

## Testing Strategy (Not Yet Implemented)

### Recommended Structure
```
src-tauri/tests/
├── integration/
│   ├── audio_recording_test.rs
│   ├── transcription_test.rs
│   └── chat_session_test.rs
└── unit/
    ├── db_repository_test.rs
    └── api_client_test.rs

src/tests/
├── privacy_scanner.test.js
└── components/
    ├── ChatPanel.test.js
    └── SettingsPanel.test.js
```

**Current Coverage**: ~5% (only basic unit tests in some modules)

**Goal**: 60%+ coverage before v1.0 release

---

## Debugging Tips

### Rust Backend Logs
```bash
# Logs go to stdout during development
npm run tauri:dev

# Or check system logs
tail -f ~/Library/Logs/braindump/app.log
```

### Frontend Console
- Open Developer Tools in running app: `Cmd+Option+I`
- Console shows: Tauri command errors, Svelte warnings, API responses

### Common Errors

**"library 'whisper' not found"**:
```bash
# Solution: Install whisper.cpp
brew install whisper-cpp
```

**"Cannot use `export let` in runes mode"**:
```bash
# Solution: Migrate to Svelte 5 runes syntax
# Change: export let prop
# To: let { prop } = $props()
```

**"API key not found"**:
```bash
# Solution: Create .env file or add via Settings panel
echo 'OPENAI_API_KEY=sk-...' > .env
npm run tauri:dev  # Auto-imports to keychain
```

---

## Quick Links

- **Project Status**: `docs/dev/PROJECT_STATUS_2025-11-16.md`
- **Missing Features**: `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`
- **Development Guide**: `docs/dev/HANDOFF_TO_WEB_TEAM.md`
- **GitHub Repo**: https://github.com/Iamcodio/IAC-031-clear-voice-app
- **Tauri Docs**: https://v2.tauri.app/
- **Svelte 5 Docs**: https://svelte.dev/docs/svelte/what-are-runes

---

**Last Updated**: 2025-11-16
**Current Branch**: `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`
**Completion Status**: 60% feature-complete, 14 features missing before v1.0
=======
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

### Budget Allocation (UPDATED: Day 1 Research)
- **Jina.ai**: $0/mo (50K pages FREE tier)
- **ScraperAPI**: $0-49/mo (fallback only)
- **OpenAI**: ~$20/mo (bulk analysis)
- **PostgreSQL**: $0 (local or Hetzner VPS $4/mo)
- **Redis**: $0 (free tier)
- **ChromaDB**: $0 (local)
- **Total MVP**: $20-89/mo (vs TweetHunter $49-99/mo, SuperX $29/mo)

**Competitive Advantage**:
- TweetHunter: Twitter-only, $49-99/mo, 5.6K users
- SuperX: Twitter-only Chrome extension, $29/mo, 9K users
- **Us**: Multi-platform (Twitter + YouTube + Reddit + Web), $20-89/mo, pattern detection

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
>>>>>>> iac032/main
