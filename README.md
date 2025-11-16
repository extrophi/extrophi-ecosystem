# IAC-032 Unified Scraper

**Multi-platform content intelligence engine for content creators, copywriters, and marketers.**

Scrapes Twitter, YouTube, Reddit, Amazon (and 20+ other sources), analyzes with LLM to extract copywriting frameworks, detects cross-platform patterns, mines authentic customer language, and generates production-ready course scripts and content briefs.

---

## Vision

This isn't just a scraper—it's **the blacksmith's forge where content empires are made.**

Research any topic by systematically analyzing the world's best creators, identifying authorities, finding content gaps, and synthesizing insights into actionable intelligence.

**The 4D Value Vortex**: Better research → better content → better engagement → more value flowing back to the community.

---

## Key Features

### Multi-Platform Scraping
- **Twitter**: OAuth-authenticated scraping with enterprise-grade stealth (reuses IAC-024 battle-tested code)
- **YouTube**: Transcript extraction + video metadata
- **Reddit**: PRAW-based community mining for pain points and VOC
- **Amazon**: Review analysis (1-3 stars = pain language, 5 stars = desire language)
- **Web/Blogs**: ScraperAPI.com integration for robust scraping
- **SERP**: Google search results for SEO intelligence

### Intelligent Analysis
- **RAG Semantic Search**: ChromaDB + pgvector for meaning-based queries
- **LLM Analysis**: OpenAI GPT-4 (bulk) + Claude Sonnet 4.5 (polish)
- **Framework Detection**: Automatically identifies AIDA, PAS, BAB, PASTOR in content
- **Hook Extraction**: Curiosity-based, specificity-based, benefit-driven hooks
- **Pattern Recognition**: Detects cross-platform elaboration (tweet → newsletter → video)
- **Authority Ranking**: Identifies top creators by engagement × content quality

### Content Generation
- **Course Script Generator**: Production-ready scripts with citations
- **Content Briefs**: Research-backed outlines for blog posts, newsletters
- **Multi-Format Export**: Markdown, tweets, video structures
- **Hemingway Analysis**: Readability scoring, passive voice detection

---

## Tech Stack

### Backend
- **FastAPI**: Async Python API framework
- **PostgreSQL + pgvector**: Production vector database
- **ChromaDB**: Local semantic search
- **Redis + RQ**: Simple job queue orchestration
- **ScraperAPI.com**: Robust web scraping ($49/mo, 100K credits)

### Platform Libraries
- **Playwright**: Browser automation (Twitter OAuth, dynamic content)
- **youtube-transcript-api**: YouTube transcript extraction
- **PRAW**: Reddit official API
- **OpenAI SDK**: GPT-4 analysis + embeddings
- **Anthropic SDK**: Claude Sonnet 4.5 copywriting analysis

### Frontend (Week 2)
- **Tauri 2.0**: Rust-based desktop framework
- **Svelte 5**: Reactive UI with runes
- **Monaco Editor**: VS Code-powered markdown editor

---

## Project Status

**Sprint**: Day 1 of 3 (Research & Architecture)
**Budget**: €900 (expires in 3 days)
**Timeline**: Nov 16-19, 2025

### Current Phase: Foundation
- [x] Repository initialized, CLAUDE.md created
- [x] GitHub Issues #1-5 created for research team
- [x] Documentation structure established
- [ ] ScraperAPI/Bright Data/Apify docs scraped (Issues #1-3)
- [ ] Platform comparison matrix (Issue #4)
- [ ] PostgreSQL schema designed
- [ ] IAC-024 Twitter scraper ported

---

## Quick Start

### For Research Team (Claude Code Web)
1. **Read context**: `CLAUDE.md` + `ORCHESTRATION.md`
2. **Check assignment**: GitHub Issues
3. **Execute task**: Follow guardrails exactly
4. **Document findings**: Update `docs/dev/` or `docs/pm/`
5. **Commit**: Use format from `ORCHESTRATION.md`

### For Developers (Week 2)
```bash
# Clone repository
git clone https://github.com/Iamcodio/IAC-032-unified-scraper.git
cd IAC-032-unified-scraper

# Python environment (use UV per CLAUDE.md)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt  # (to be created Day 2)

# PostgreSQL + pgvector
brew install postgresql@16 pgvector
createdb unified_scraper

# Run backend API (Day 2+)
uvicorn backend.api.main:app --reload

# Run doc scraper tool (now)
cd tools/doc-scraper
uv venv && source .venv/bin/activate
python scrape_docs.py
```

---

## Documentation

### For Project Management
- **`CLAUDE.md`**: Comprehensive project context for Claude Code instances
- **`ORCHESTRATION.md`**: Team execution guide with guardrails
- **`docs/pm/PRD_PROPER.md`**: Product requirements (source of truth)
- **`docs/pm/README.md`**: PM workflow and decision log

### For Development
- **`docs/dev/`**: Scraped API docs (ScraperAPI, Bright Data, Apify, Tauri, Svelte)
- **`tools/doc-scraper/`**: Documentation scraping tool

### For Research
- **`docs/research/`**: Dan Koe methodology, RMBC framework, platform comparisons

---

## GitHub Workflow

### Issues
- **#1**: Scrape ScraperAPI.com docs
- **#2**: Scrape Bright Data docs
- **#3**: Scrape Apify docs
- **#4**: Create comparison matrix
- **#5**: Setup CI/CD guardrails

### Commit Format
```
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `docs`, `feat`, `fix`, `refactor`, `test`, `chore`

---

## Architecture

### Unified Content Schema
All platforms normalize to:
```python
{
  "content_id": "uuid",
  "platform": "twitter|youtube|reddit|amazon",
  "source_url": "https://...",
  "author": {...},
  "content": {"title": "...", "body": "..."},
  "metrics": {"likes": 100, "engagement_score": 1234},
  "analysis": {"frameworks": ["AIDA"], "hooks": [...]},
  "embedding": [0.123, ...],  # 1536 dimensions
  "scraped_at": "2025-11-16T..."
}
```

### Plugin Pattern
Each platform = adapter implementing `BaseScraper`:
- `extract(url) -> dict`: Scrape raw data
- `normalize(raw_data) -> UnifiedContent`: Convert to schema

Adding new platforms: ~30 minutes per adapter.

---

## Reusable Code from IAC-024

**Location**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/`

**Critical files to port**:
1. `src/scrapers/persistent_x_session.py` (1,231 lines)
   - Enterprise Twitter scraping with fingerprint spoofing
   - Human behavior simulation
   - Session health monitoring

2. `src/scrapers/playwright_oauth_client.py` (534 lines)
   - Google OAuth for @iamcodio account
   - Chrome profile persistence

3. `src/database/schema.py` + `src/models/tweet_models.py`
   - Proven database patterns
   - Pydantic models

See `CLAUDE.md` for detailed porting strategy.

---

## Budget & Costs

### Monthly Operational ($69)
- ScraperAPI Hobby: $49/mo (100K credits, 20K pages)
- OpenAI API: ~$20/mo (GPT-4 analysis + embeddings)
- PostgreSQL: $0 (local or Hetzner $4/mo)
- Redis: $0 (free tier)
- ChromaDB: $0 (local)

### 3-Day Sprint
- ScraperAPI: 5K credits used / 100K = 5%
- OpenAI: ~$5 analysis
- Total: ~$54 spent

---

## Success Criteria (Day 3 MVP)

**Backend API**:
- [ ] `/scrape/twitter/{username}` → 100 tweets stored
- [ ] `/scrape/youtube/{video_id}` → transcript + metadata
- [ ] `/scrape/reddit/{subreddit}` → 50 posts
- [ ] `/query/rag?prompt=...` → semantic search results
- [ ] `/analyze/patterns` → cross-platform elaboration
- [ ] `/generate/course-script` → production script
- [ ] `/export/markdown` → formatted document

**Quality**:
- [ ] Modular adapters (30 min to add platforms)
- [ ] Type-safe Pydantic models
- [ ] Proper error handling + retry logic
- [ ] Clean documentation

---

## Contributing

This project uses a **research → document → command** workflow:

1. **Claude Desktop (Technical Lead)**: Research, architecture, documentation
2. **Claude Code Web (Execution Team)**: Implementation via GitHub Issues
3. **CI/CD**: Automated testing and deployment

See `ORCHESTRATION.md` for contribution guidelines.

---

## License

Private project - All rights reserved

---

## Contact

**GitHub**: [@iamcodio](https://github.com/Iamcodio)
**Project**: IAC-032 Unified Scraper
**Status**: Active Development (3-day sprint)

---

*Built with Claude Code - The blacksmith's forge for content empires.*
