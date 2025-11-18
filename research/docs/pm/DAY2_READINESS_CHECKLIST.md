# Day 2 Readiness Checklist

**Sprint**: Day 2 of 3 - Multi-Platform Implementation
**Target Start**: After CCW research completes
**Estimated Duration**: 8 hours (6 parallel packages)

---

## Pre-Flight Checks

### ✅ Day 1 Foundation Complete

- [x] **CLAUDE.md** created (500 lines project context)
- [x] **ORCHESTRATION.md** created (execution guardrails)
- [x] **DATABASE_SCHEMA.md** designed (PostgreSQL + pgvector)
- [x] **API_SPECIFICATIONS.md** documented (700 lines)
- [x] **IAC024_PORTING_STRATEGY.md** detailed (Twitter code reuse)
- [x] **DAY2_WORK_PACKAGES.md** created (6 parallel tasks)
- [x] **DAY1_PROGRESS_SUMMARY.md** documented (630 lines recap)
- [x] All files committed and pushed to GitHub main branch

### ⏳ Awaiting CCW Research Completion

**9 GitHub Issues** (all currently open):
- [ ] #1: ScraperAPI docs research
- [ ] #2: Bright Data docs research
- [ ] #3: Apify docs research
- [ ] #4: Platform comparison matrix synthesis
- [ ] #5: GitHub Actions CI/CD (deferred to Day 2)
- [ ] #6: Jina.ai docs research
- [ ] #7: SuperX.so competitor analysis
- [ ] #8: TweetHunter.io competitor analysis
- [ ] #9: DataForSEO docs research

**Expected Outputs** (check when research completes):
- [ ] `docs/dev/scraperapi/*.md` exists (10+ files)
- [ ] `docs/dev/brightdata/*.md` exists (8+ files)
- [ ] `docs/dev/apify/*.md` exists (8+ files)
- [ ] `docs/dev/jina/*.md` exists (5+ files)
- [ ] `docs/dev/dataforseo/*.md` exists (6+ files)
- [ ] `docs/research/SUPERX_ANALYSIS.md` created
- [ ] `docs/research/TWEETHUNTER_ANALYSIS.md` created
- [ ] `docs/pm/MASTER_RESEARCH_SYNTHESIS.md` created (CRITICAL)

---

## When Research Completes (Do This First)

### 1. Review Research Outputs (30 minutes)

**Platform Documentation**:
```bash
# Check scraperapi docs
ls -la docs/dev/scraperapi/
# Expected: getting-started.md, api-reference.md, structured-data.md, etc.

# Check bright data docs
ls -la docs/dev/brightdata/
# Expected: web-scraper-api.md, proxy-network.md, pricing.md, etc.

# Check apify docs
ls -la docs/dev/apify/
# Expected: actors.md, web-scraper.md, integrations.md, etc.

# Check jina docs (FREE tier!)
ls -la docs/dev/jina/
# Expected: reader-api.md, free-tier.md, rate-limits.md, etc.

# Check dataforseo docs (SERP specialist)
ls -la docs/dev/dataforseo/
# Expected: serp-api.md, google-search.md, competitors.md, etc.
```

**Competitor Intelligence**:
```bash
# Read SuperX analysis
cat docs/research/SUPERX_ANALYSIS.md
# Expected: Feature comparison, pricing, tech stack, market positioning

# Read TweetHunter analysis
cat docs/research/TWEETHUNTER_ANALYSIS.md
# Expected: 3M viral tweets DB, AI21 Labs model, pricing tiers, unique features
```

**CRITICAL - Platform Recommendation**:
```bash
# Read master synthesis
cat docs/pm/MASTER_RESEARCH_SYNTHESIS.md
# Expected:
# - ScraperAPI vs Bright Data vs Apify cost/feature matrix
# - Jina.ai FREE tier recommendation (10M tokens/month)
# - DataForSEO integration strategy (SERP intelligence)
# - Final platform selection with rationale
```

### 2. Update CLAUDE.md (15 minutes)

**Add research findings**:
- [ ] Update "ScraperAPI Integration Patterns" section with actual API usage
- [ ] Add "Jina.ai Free Tier Strategy" section (10M tokens = huge savings)
- [ ] Add "DataForSEO SERP Intelligence" section (competitive analysis)
- [ ] Update "Budget Allocation" with final platform costs
- [ ] Add "Competitor Positioning" section (vs SuperX, TweetHunter)

**Example additions**:
```markdown
## Jina.ai Free Tier Strategy (Added After Research)

**FREE Credits**: 10M tokens/month = ~$200/mo value
**Best Use Cases**:
- Blog content extraction (simple HTML)
- Documentation scraping (markdown conversion)
- Article parsing (no JS rendering needed)

**When to use ScraperAPI instead**:
- Complex JS-rendered sites (Twitter, Amazon)
- Anti-bot protection (fingerprinting required)
- Structured data extraction (Amazon reviews, Google SERP)

## DataForSEO Integration (Added After Research)

**Pricing**: $X per 1K SERP queries
**Use Cases**:
- Content gap analysis (what ranks vs what authorities say)
- Keyword opportunity detection
- Competitive intelligence (who owns topic space)
```

### 3. Close GitHub Issues (5 minutes)

```bash
# Close research issues after verification
env -u GITHUB_TOKEN gh issue close 1 --comment "Research complete, docs in docs/dev/scraperapi/"
env -u GITHUB_TOKEN gh issue close 2 --comment "Research complete, docs in docs/dev/brightdata/"
env -u GITHUB_TOKEN gh issue close 3 --comment "Research complete, docs in docs/dev/apify/"
env -u GITHUB_TOKEN gh issue close 6 --comment "Research complete, docs in docs/dev/jina/"
env -u GITHUB_TOKEN gh issue close 9 --comment "Research complete, docs in docs/dev/dataforseo/"
env -u GITHUB_TOKEN gh issue close 7 --comment "Competitor analysis complete, see docs/research/SUPERX_ANALYSIS.md"
env -u GITHUB_TOKEN gh issue close 8 --comment "Competitor analysis complete, see docs/research/TWEETHUNTER_ANALYSIS.md"
env -u GITHUB_TOKEN gh issue close 4 --comment "Synthesis complete, see docs/pm/MASTER_RESEARCH_SYNTHESIS.md"

# Keep #5 open (GitHub Actions deferred to Day 2)
```

---

## Day 2 Execution Plan

### CRITICAL: Package 1 MUST Complete First

**Package 1: Database Setup** (1-2 hours)
- PostgreSQL installation
- pgvector extension
- Schema creation from `DATABASE_SCHEMA.md`
- Connection pooling
- Test queries (vector similarity search)

**Why CRITICAL**: Packages 2-6 all depend on database

**Deliverables**:
- `backend/db/connection.py` - Database connection manager
- `backend/db/models.py` - SQLAlchemy models
- `backend/db/schema.sql` - Table definitions
- Working connection: `psql unified_scraper -c "SELECT version();"`

### After Package 1: Spawn 5 Parallel Agents

**Package 2: Twitter Scraper** (3-4 hours)
- Port `persistent_x_session.py` (1,231 lines)
- Wrap in `BaseScraper` interface
- Test with @dankoe (scrape 10 tweets)
- Store in PostgreSQL with unified schema

**Package 3: FastAPI Scaffold** (2-3 hours)
- Project structure (routers, services, middleware)
- `/scrape` universal endpoint
- `/query/rag` semantic search endpoint
- CORS, error handling, logging

**Package 4: YouTube Scraper** (2-3 hours)
- `youtube-transcript-api` integration
- `yt-dlp` metadata extraction
- Transcript chunking (vector indexing)
- Normalize to UnifiedContent

**Package 5: Reddit Scraper** (1-2 hours)
- PRAW setup (OAuth 1,000 req/10min)
- Subreddit scraping (r/productivity, r/Entrepreneur)
- Post + comment extraction
- Normalize to UnifiedContent

**Package 6: ChromaDB RAG** (2-3 hours)
- Collection creation
- OpenAI embedding generation
- Document indexing (chunking strategy)
- Similarity search queries

---

## Day 2 Work Package Execution (CCW Instructions)

### Package 1: Database Setup

**CCW Prompt**:
```markdown
# Package 1: Database Setup

**Repository**: Iamcodio/IAC-032-unified-scraper
**Reference**: docs/pm/DAY2_WORK_PACKAGES.md (Package 1)
**Schema**: docs/pm/DATABASE_SCHEMA.md
**Duration**: 1-2 hours

## Objective
Set up PostgreSQL database with pgvector extension and create unified content schema.

## Tasks
1. Install PostgreSQL 16 + pgvector extension
2. Create database `unified_scraper`
3. Create tables from DATABASE_SCHEMA.md
4. Implement connection pooling (SQLAlchemy)
5. Test vector similarity queries

## Deliverables
- backend/db/connection.py
- backend/db/models.py
- backend/db/schema.sql
- Working psql connection

## Success Criteria
- `psql unified_scraper -c "SELECT version();"` succeeds
- Vector index created: `idx_contents_embedding`
- Sample similarity query returns results

## Commit Format
```
feat(db): Setup PostgreSQL with pgvector

- Install PostgreSQL 16 + pgvector extension
- Create unified_scraper database
- Implement SQLAlchemy models with vector support
- Add connection pooling (max 10 connections)
- Test vector similarity search (<=> operator)

Tables: contents, authors, projects, patterns
Indexes: vector (ivfflat), platform, author_id

Ref: docs/pm/DATABASE_SCHEMA.md, Package 1
```
```

### Packages 2-6: Parallel Execution

**After Package 1 completes, spawn 5 CCW agents simultaneously**:

**Agent 1**: Package 2 (Twitter Scraper)
**Agent 2**: Package 3 (FastAPI Scaffold)
**Agent 3**: Package 4 (YouTube Scraper)
**Agent 4**: Package 5 (Reddit Scraper)
**Agent 5**: Package 6 (ChromaDB RAG)

**All agents read**:
- `CLAUDE.md` (project context)
- `ORCHESTRATION.md` (execution guardrails)
- `docs/pm/DAY2_WORK_PACKAGES.md` (detailed package instructions)

---

## Environment Setup (Package 1 Agent)

### PostgreSQL Installation

**macOS (Homebrew)**:
```bash
brew install postgresql@16 pgvector
brew services start postgresql@16

# Create database
createdb unified_scraper

# Install pgvector extension
psql unified_scraper -c "CREATE EXTENSION vector;"
```

**Linux (Ubuntu)**:
```bash
sudo apt install postgresql-16 postgresql-16-pgvector
sudo systemctl start postgresql

# Create database
sudo -u postgres createdb unified_scraper
sudo -u postgres psql unified_scraper -c "CREATE EXTENSION vector;"
```

### Python Environment

```bash
cd /Users/kjd/01-projects/IAC-032-unified-scraper/backend
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install fastapi uvicorn sqlalchemy psycopg2-binary pgvector
uv pip install openai chromadb pydantic python-dotenv redis rq
uv pip install playwright beautifulsoup4 requests praw youtube-transcript-api yt-dlp
```

---

## Success Criteria (End of Day 2)

### Database
- [ ] PostgreSQL running with pgvector extension
- [ ] All tables created (contents, authors, projects, patterns)
- [ ] Vector indexes working (cosine similarity < 100ms)
- [ ] Sample data inserted (10 test records)

### Scrapers
- [ ] Twitter: Scrape @dankoe → 10 tweets stored
- [ ] YouTube: Extract transcript from test video
- [ ] Reddit: Scrape r/productivity → 20 posts stored
- [ ] All scrapers implement BaseScraper interface
- [ ] All scrapers normalize to UnifiedContent schema

### API
- [ ] FastAPI running on http://localhost:8000
- [ ] POST /scrape works for all platforms
- [ ] GET /docs shows Swagger UI
- [ ] Error handling returns proper status codes
- [ ] CORS configured for frontend

### RAG
- [ ] ChromaDB collection created
- [ ] OpenAI embeddings generated (1536 dims)
- [ ] Semantic search query "focus systems" returns results
- [ ] Similarity threshold working (>0.85 = elaboration)

### Code Quality
- [ ] Type hints on all functions
- [ ] Pydantic models validate input
- [ ] Proper error handling (try/except)
- [ ] Logging configured (INFO level)
- [ ] README.md updated with setup instructions

---

## Risk Mitigation

### Risk: PostgreSQL Setup Complexity
**Mitigation**: Package 1 has detailed installation commands for macOS/Linux
**Fallback**: Use SQLite + sqlite-vss if PostgreSQL fails (Day 3 migration)

### Risk: IAC-024 Code Port Fails
**Mitigation**: Keep IAC-024 running in parallel, can test comparison
**Fallback**: Use simple requests library (no anti-detection) for MVP

### Risk: Vector Index Performance
**Mitigation**: Start with IVFFlat (fast), upgrade to HNSW if slow
**Fallback**: Use ChromaDB only (skip PostgreSQL vectors)

### Risk: Parallel Agents Conflict
**Mitigation**: ORCHESTRATION.md has clear file ownership (no overlapping edits)
**Fallback**: Run Packages 2-6 sequentially if conflicts occur

---

## Budget Tracking (Day 2)

**Estimated Day 2 Costs**:
- CCW execution (6 packages, 8 hours): €200-250
- OpenAI embeddings (test data): €5-10
- ScraperAPI credits (testing): €0 (trial)
- **Total Day 2**: €205-260

**Remaining Budget**: €885 - €260 = €625 for Day 3

**On Track**: ✅ YES (Day 3 only needs €150-200)

---

## Next Session Actions

**When you resume after CCW research completes**:

1. ✅ Review research outputs (30 min)
2. ✅ Update CLAUDE.md with findings (15 min)
3. ✅ Close issues #1-4, #6-9 (5 min)
4. ✅ Create Package 1 CCW prompt (10 min)
5. ✅ Spawn Package 1 agent (start execution)
6. ⏳ Wait for Package 1 completion (1-2 hours)
7. ✅ Spawn Packages 2-6 in parallel (start execution)
8. ⏳ Monitor progress (8 hours total)
9. ✅ Review deliverables, update SESSION_STATUS.md
10. ✅ Commit Day 2 completion summary

---

**Day 2 Readiness: ✅ FULLY PREPARED**
**Awaiting: CCW research completion**
**Next: Review synthesis → Launch Package 1 → Parallel execution**
