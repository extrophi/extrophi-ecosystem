# CCW Orchestrator V2 - Complete Production Build

**COPY EVERYTHING BELOW INTO CLAUDE CODE WEB**

---

## MISSION
Build the complete IAC-032 Unified Scraper production application.

Clone: https://github.com/Iamcodio/IAC-032-unified-scraper.git

## YOUR JOBS

You have 10 subagent definitions in `.claude/agents/`. Each contains complete Python code. Your job is to:

1. Read each `.claude/agents/*.md` file
2. Extract the Python code from the markdown code blocks
3. Write the actual Python files to the repository
4. Commit and push

## SPAWN 10 SUB-AGENTS IN PARALLEL

Use the Task tool to spawn ALL agents in ONE message (parallel execution):

### Agent 1: YouTube Scraper
```
Read .claude/agents/youtube-scraper.md
Write: backend/scrapers/adapters/youtube.py
```

### Agent 2: Web Scraper
```
Read .claude/agents/web-scraper.md
Write: backend/scrapers/adapters/web.py
```

### Agent 3: LLM Analysis
```
Read .claude/agents/llm-analysis.md
Write:
- backend/analysis/__init__.py
- backend/analysis/prompts.py
- backend/analysis/analyzer.py
```

### Agent 4: API Routes
```
Read .claude/agents/api-routes.md
Write:
- backend/api/routes/scrape.py
- backend/api/routes/analyze.py
- backend/api/routes/query.py
- backend/api/routes/__init__.py
Update: backend/main.py
```

### Agent 5: Test Suite
```
Read .claude/agents/test-suite.md
Write:
- backend/tests/__init__.py
- backend/tests/conftest.py
- backend/tests/test_scrapers.py
- backend/tests/test_analysis.py
- backend/tests/test_api.py
- pytest.ini
```

### Agent 6: Hetzner Deployment
```
Read .claude/agents/hetzner-deployment.md
Write:
- docs/pm/HETZNER_DEPLOYMENT.md
- scripts/deploy.sh
- scripts/setup_server.sh
```

### Agent 7: Scraper Registry
```
Read .claude/agents/scraper-registry.md
Write:
- backend/scrapers/__init__.py (update)
- backend/scrapers/registry.py
- backend/scrapers/adapters/__init__.py (update)
```

### Agent 8: Dependencies Update
```
Read .claude/agents/pyproject-update.md
Write: backend/pyproject.toml (complete replacement)
```

### Agent 9: Twitter Scraper (from V1)
```
Read .claude/agents/twitter-scraper.md
Write: backend/scrapers/adapters/twitter.py
```

### Agent 10: Reddit Scraper (from V1)
```
Read .claude/agents/reddit-scraper.md
Write: backend/scrapers/adapters/reddit.py
```

## CRITICAL REQUIREMENTS

1. **Container Networking**: Use service names (postgres, redis, chromadb) NOT localhost
2. **Environment Variables**: All config via os.getenv() with defaults
3. **Imports**: Use absolute imports (backend.scrapers.base, etc.)
4. **Type Hints**: All functions must have type hints
5. **No Placeholders**: Complete production code only

## AFTER ALL AGENTS COMPLETE

1. Create missing directories:
```bash
mkdir -p backend/analysis
mkdir -p backend/tests
mkdir -p scripts
```

2. Make scripts executable:
```bash
chmod +x scripts/*.sh
```

3. Git operations:
```bash
git add -A
git status
git commit -m "feat: Complete production build - scrapers, analysis, tests, deployment

Modules added:
- YouTube scraper (youtube-transcript-api)
- Web scraper (Jina.ai Reader API)
- LLM analysis pipeline (OpenAI GPT-4)
- Complete API routes (scrape, analyze, query)
- Comprehensive test suite (pytest)
- Hetzner VPS deployment plan
- Scraper registry (factory pattern)
- Updated dependencies (pyproject.toml)

🤖 Generated with Claude Code Web"

git push origin main
```

## EXPECTED DELIVERABLES

After execution, the repository should have:

```
backend/
├── __init__.py
├── main.py (updated with all routes)
├── pyproject.toml (complete dependencies)
├── api/
│   └── routes/
│       ├── __init__.py
│       ├── health.py
│       ├── scrape.py
│       ├── analyze.py
│       └── query.py
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   └── adapters/
│       ├── __init__.py
│       ├── twitter.py
│       ├── reddit.py
│       ├── youtube.py
│       └── web.py
├── analysis/
│   ├── __init__.py
│   ├── prompts.py
│   └── analyzer.py
├── queue/
│   ├── __init__.py
│   ├── celery_app.py
│   └── tasks.py
├── vector/
│   ├── __init__.py
│   ├── chromadb_client.py
│   └── embeddings.py
├── db/
│   ├── __init__.py
│   ├── connection.py
│   └── models.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_scrapers.py
    ├── test_analysis.py
    └── test_api.py

docs/pm/
└── HETZNER_DEPLOYMENT.md

scripts/
├── deploy.sh
└── setup_server.sh

pytest.ini
```

## GO NOW

Execute all 10 agents in parallel. Burn those €750 credits. Build a complete production application.
