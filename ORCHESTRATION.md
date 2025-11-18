# Orchestration Guide for Claude Code Web (CCW) Team

**Audience**: Claude Code Web agents executing Day 1-3 sprint tasks

---

## Mission

Build a multi-platform content intelligence engine in 3 days (€900 budget) that scrapes Twitter/YouTube/Reddit/Amazon, analyzes content with LLM, detects patterns, and generates course scripts.

**Your role**: Execute research and implementation tasks assigned via GitHub Issues.

**Manager's role**: Technical lead (Claude Desktop) provides architecture, reviews work, synthesizes findings.

---

## Workflow

1. **Receive Assignment**: Check GitHub Issues for tasks assigned to you
2. **Read Context**: Review CLAUDE.md (project overview), PRD_PROPER.md (requirements)
3. **Execute**: Follow issue description EXACTLY - respect guardrails
4. **Document**: Update relevant docs (CLAUDE.md, docs/pm/, docs/dev/)
5. **Commit**: Descriptive message following format below
6. **Update Issue**: Comment with progress, close when complete

---

## Guardrails (DO NOT VIOLATE)

### Research Tasks (Issues #1-3)
- ✅ Use ONLY `tools/doc-scraper/scrape_docs.py`
- ✅ Extend `DOCS_TO_SCRAPE` config dictionary
- ✅ Output to `docs/dev/{platform}/`
- ❌ DO NOT modify scraper core logic
- ❌ DO NOT install new dependencies
- ❌ DO NOT create new tools from scratch

### Documentation Tasks
- ✅ Update CLAUDE.md with synthesized findings
- ✅ Create comparison matrices in docs/pm/
- ✅ Use markdown tables, bullet points, clear structure
- ❌ DO NOT delete existing content
- ❌ DO NOT create duplicate sections

### Code Implementation (Day 2-3)
- ✅ Follow architecture in PRD_PROPER.md
- ✅ Reuse IAC-024 code patterns (see CLAUDE.md)
- ✅ Type hints (Pydantic models, function signatures)
- ❌ DO NOT deviate from PostgreSQL + FastAPI stack
- ❌ DO NOT skip error handling
- ❌ DO NOT commit secrets (.env files)

---

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types
- `docs`: Documentation changes (CLAUDE.md, research docs, README)
- `feat`: New feature (scraper adapter, API endpoint)
- `fix`: Bug fix
- `refactor`: Code improvement without behavior change
- `test`: Test additions
- `chore`: Build config, dependencies

### Examples
```bash
# Research task
docs(scraperapi): Add official API documentation

Scraped docs.scraperapi.com using doc-scraper tool.
Output: 12 markdown files in docs/dev/scraperapi/

Key findings:
- Structured endpoints for Amazon/Google/eBay
- JS rendering costs +5 credits per request
- Rate limit: 20 concurrent threads on Hobby plan

Related: #1

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

```bash
# Analysis task
docs(pm): Add scraper platform comparison matrix

Compared ScraperAPI vs Bright Data vs Apify across:
- Pricing: ScraperAPI $0.00049/req, Bright Data $0.001/req
- Features: ScraperAPI has best structured endpoints
- Reliability: All 99%+ uptime SLAs

Recommendation: ScraperAPI for MVP (cost + ease of use)

Output: docs/pm/SCRAPER_COMPARISON.md

Related: #4, closes #1, #2, #3

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## File Structure Reference

```
IAC-032-unified-scraper/
├── CLAUDE.md              # Project context (READ FIRST)
├── ORCHESTRATION.md       # This file (execution guide)
├── .gitignore             # Git ignore rules
│
├── docs/
│   ├── pm/                # Project management (for you + manager + PM)
│   │   ├── README.md
│   │   ├── PRD_PROPER.md  # SOURCE OF TRUTH requirements
│   │   ├── PRD_v2.md      # IGNORE (deprecated)
│   │   └── SCRAPER_COMPARISON.md  # Your output (Issue #4)
│   │
│   ├── dev/               # Development docs (your research output)
│   │   ├── README.md
│   │   ├── scraperapi/    # Issue #1 output
│   │   ├── brightdata/    # Issue #2 output
│   │   └── apify/         # Issue #3 output
│   │
│   └── research/          # Background research (read-only)
│
├── tools/
│   └── doc-scraper/       # Documentation scraping tool
│       ├── scrape_docs.py # Extend DOCS_TO_SCRAPE here
│       └── pyproject.toml
│
└── backend/               # (Day 2-3: you'll create this)
    ├── api/               # FastAPI application
    ├── scrapers/          # Platform adapters
    ├── models/            # Pydantic schemas
    ├── db/                # PostgreSQL connection
    └── llm/               # LLM analysis
```

---

## Communication Protocol

### With Manager (Claude Desktop)
- **Ask questions**: Comment on GitHub Issues if unclear
- **Report blockers**: Tag issue with problem description
- **Request review**: PR for code changes, issue comment for docs

### With PM (Human)
- **Status updates**: Issue comments only (manager handles direct communication)
- **Blockers**: Report to manager via issue, manager escalates if needed

### With Other Agents
- **Coordinate**: Check issue dependencies (e.g., #4 depends on #1-3)
- **Avoid conflicts**: Don't work on same files simultaneously
- **Review**: Comment on related PRs with feedback

---

## Success Criteria

### Day 1 (Research & Architecture)
- [ ] Issues #1-3 completed (ScraperAPI, Bright Data, Apify docs scraped)
- [ ] Issue #4 completed (comparison matrix with recommendation)
- [ ] Issue #5 completed (CI/CD workflow preventing off-track work)
- [ ] CLAUDE.md updated with synthesized research findings
- [ ] PostgreSQL schema designed (docs/pm/DATABASE_SCHEMA.md)

### Day 2 (Multi-Platform Implementation)
- [ ] Twitter scraper (IAC-024 code ported)
- [ ] YouTube scraper (youtube-transcript-api)
- [ ] Reddit scraper (PRAW)
- [ ] ChromaDB RAG integration
- [ ] FastAPI endpoints functional

### Day 3 (Intelligence & Export)
- [ ] Authority detection working
- [ ] Course script generator outputs production-ready scripts
- [ ] Pattern detection identifying cross-platform elaboration
- [ ] All tests passing, documentation complete

---

## Emergency Procedures

### If You Get Stuck
1. **Read CLAUDE.md** - 90% of questions answered there
2. **Check PRD_PROPER.md** - Requirements clarity
3. **Review IAC-024 code** - Patterns to reuse
4. **Comment on issue** - Manager will respond
5. **STOP if unclear** - Don't guess, ask

### If Guardrails Prevent Progress
- **Report immediately**: "Guardrail X prevents Y, need guidance"
- **Don't bypass**: Manager will adjust scope or provide workaround
- **Document**: Explain what you tried, why it failed

### If Timeline Slips
- **Prioritize**: Focus on must-haves (Twitter > YouTube > Reddit > Amazon)
- **Communicate**: Issue comment with revised estimate
- **Defer**: Suggest moving stretch goals to Week 2

---

## Quick Commands

```bash
# Setup doc-scraper
cd tools/doc-scraper
uv venv && source .venv/bin/activate
uv pip install beautifulsoup4 markitdown requests

# Run scraper (after extending DOCS_TO_SCRAPE config)
python scrape_docs.py

# Check GitHub issues
gh issue list

# Create branch for work
git checkout -b feature/scraperapi-docs

# Commit with proper format
git commit -m "docs(scraperapi): Add API documentation

Scraped docs.scraperapi.com...
Related: #1

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push and create PR
git push origin feature/scraperapi-docs
gh pr create --title "docs: Add ScraperAPI documentation" --body "Closes #1"
```

---

## Remember

- **You're part of a team** - Your work enables Day 2-3 implementation
- **Quality > Speed** - Clean docs save hours downstream
- **Guardrails exist for a reason** - They prevent wasted effort
- **Manager has your back** - Ask questions, report blockers
- **€900 deadline is real** - Focus, no scope creep

**LET'S BUILD THE BLACKSMITH'S FORGE.**

---

*Last updated: 2025-11-16*
*Manager: Claude Desktop (Technical Lead)*
*PM: @iamcodio*
