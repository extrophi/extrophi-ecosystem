# Project Management Documentation

This directory contains project management documents for orchestrating the IAC-032 Unified Scraper build.

## Audience

**For**: Project manager (you), technical lead (Claude Desktop), execution team (Claude Code Web agents)

## Documents

### PRD_PROPER.md (SOURCE OF TRUTH)
- **Purpose**: Authoritative product requirements document
- **Architecture**: Tauri + Rust + Python multi-platform scraper
- **Timeline**: 3-day sprint (Day 1-3 breakdown)
- **Budget**: €900 expires in 3 days
- **Stack**: FastAPI + PostgreSQL + pgvector + ScraperAPI.com
- **Status**: ✅ Active, being executed

### PRD_v2.md (DEPRECATED)
- **Purpose**: Alternative RAG-focused design
- **Architecture**: PyQt + SQLite + 2TB course library indexing
- **Status**: ❌ Superseded by PRD_PROPER, kept for reference only
- **Note**: Do NOT implement this version

## Decision Log

### 2025-11-16: Technology Stack Finalized
- **Database**: PostgreSQL + pgvector (chosen over SQLite for production readiness)
- **Frontend**: Deferred to Week 2 (Tauri + Svelte)
- **Testing**: API-only with cURL/Postman for 3-day MVP
- **Platforms**: Twitter (IAC-024 reuse) + YouTube + Reddit (must-have Day 3)
- **Scraping**: ScraperAPI.com primary ($49/mo), direct Playwright backup

### 2025-11-16: Workflow Model Established
- **Claude Desktop (this instance)**: Research → Document → Command
- **Claude Code Web (execution team)**: Implement → Test → Deploy
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Communication**: GitHub Issues for task assignment, CLAUDE.md for context

## Sprint Management

### Day 1 (2025-11-16): Foundation + Research
- [x] Initialize repository, create CLAUDE.md
- [ ] Scrape ScraperAPI, Bright Data, Apify docs
- [ ] Create comparison matrix
- [ ] PostgreSQL schema design
- [ ] IAC-024 code porting plan

### Day 2: Multi-Platform Implementation
- [ ] YouTube scraper (youtube-transcript-api)
- [ ] Reddit scraper (PRAW)
- [ ] ChromaDB RAG integration
- [ ] LLM analysis pipeline (OpenAI GPT-4)

### Day 3: Intelligence & Export
- [ ] Authority detection algorithm
- [ ] Content gap analysis
- [ ] Course script generator
- [ ] Multi-format export (markdown, tweets, scripts)

## Communication Protocol

### For Claude Code Web Agents
1. Check GitHub Issues for assigned tasks
2. Read CLAUDE.md for project context
3. Reference PRD_PROPER.md for requirements
4. Execute, commit with descriptive messages
5. Update issue status on completion

### For Project Manager
- **docs/pm/**: Strategic decisions, sprint planning
- **GitHub Issues**: Task tracking, agent assignments
- **CLAUDE.md**: Living documentation, research synthesis
- **Pull Requests**: Code review, quality gates

**Last updated**: 2025-11-16
