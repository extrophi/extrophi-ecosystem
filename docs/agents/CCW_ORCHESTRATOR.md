# CCW Orchestrator Instructions

**COPY EVERYTHING BELOW INTO CLAUDE CODE WEB**

---

Clone https://github.com/Iamcodio/IAC-032-unified-scraper.git

Read these 4 files in .claude/agents/:
- twitter-scraper.md
- reddit-scraper.md
- queue-system.md
- vector-store.md

Each file contains complete Python code in markdown code blocks.

YOUR JOB: Extract the code from those files and write the actual Python modules.

Use the Task tool to spawn 4 sub-agents IN PARALLEL (one message, 4 tool calls):

## Agent 1: Twitter Scraper
```
Read .claude/agents/twitter-scraper.md
Extract the Python code from the code block
Write to: backend/scrapers/adapters/twitter.py
```

## Agent 2: Reddit Scraper
```
Read .claude/agents/reddit-scraper.md
Extract the Python code from the code block
Write to: backend/scrapers/adapters/reddit.py
```

## Agent 3: Queue System
```
Read .claude/agents/queue-system.md
Extract the Python code from the code blocks
Write to:
- backend/queue/__init__.py
- backend/queue/celery_app.py
- backend/queue/tasks.py
```

## Agent 4: Vector Store
```
Read .claude/agents/vector-store.md
Extract the Python code from the code blocks
Write to:
- backend/vector/__init__.py
- backend/vector/chromadb_client.py
- backend/vector/embeddings.py
```

## CRITICAL REQUIREMENTS:
- Container networking: postgres, redis, chromadb (NOT localhost)
- Import from backend.scrapers.base (already exists)
- All code is in the .claude/agents/*.md files - just extract and write it

## After all 4 agents complete:

Update backend/pyproject.toml dependencies:
```toml
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "pgvector>=0.2.0",
    "pydantic>=2.0.0",
    "redis>=5.0.0",
    "playwright>=1.40.0",
    "praw>=7.7.0",
    "celery>=5.3.0",
    "chromadb>=0.4.0",
    "openai>=1.0.0",
]
```

Then commit and push:
```bash
git add -A
git commit -m "feat: Add Twitter, Reddit, Queue, Vector modules (CCW parallel agents)"
git push origin main
```

GO NOW.
