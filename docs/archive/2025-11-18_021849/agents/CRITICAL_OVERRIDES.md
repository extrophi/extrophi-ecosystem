# CRITICAL OVERRIDES - READ FIRST

**ALL AGENTS MUST FOLLOW THESE RULES**

---

## DEPLOYMENT ENVIRONMENT

**TARGET**: Hetzner VPS (Ubuntu Server)
**CI/CD**: GitHub Actions (Ubuntu runners)
**Containerization**: Podman (NOT Docker daemon)

**NO LOCAL DEVELOPMENT** - Everything runs in containers or CI/CD.

---

## FORBIDDEN PATTERNS

### ❌ DO NOT USE:
- `brew install` - No macOS, no Homebrew
- Local filesystem paths (`/Users/kjd/...`)
- macOS-specific tools
- pip install (use UV)
- Direct database connections from local machine
- Any assumption of local development environment

### ✅ USE INSTEAD:
- **UV for Python**: `uv sync`, `uv pip install`, `uv run`
- **Podman containers**: All services run in containers
- **Environment variables**: Database URLs, API keys
- **GitHub-relative paths**: Paths relative to repo root
- **Ubuntu packages**: apt-get for system deps

---

## DATABASE SETUP

**DO NOT**:
```bash
# WRONG - macOS local
brew install postgresql@16
createdb unified_scraper_dev
psql -c "CREATE EXTENSION vector;"
```

**DO**:
```yaml
# CORRECT - Containerized service (GitHub Actions CI)
services:
  postgres:
    image: pgvector/pgvector:pg16
    env:
      POSTGRES_DB: unified_scraper
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
    ports:
      - "5432:5432"
```

Database runs in **pgvector/pgvector:pg16** container, not local install.

---

## CODE REQUIREMENTS

### 1. No Local Paths
```python
# ❌ WRONG
DATABASE_URL = "postgresql://localhost:5432/unified_scraper_dev"

# ✅ CORRECT
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://scraper:scraper_pass@postgres:5432/unified_scraper"
)
```

### 2. Container Service Names
- Database host: `postgres` (not localhost)
- Redis host: `redis` (not localhost)
- ChromaDB host: `chromadb` (not localhost)

### 3. Environment Variables
All configuration via `.env` or GitHub Secrets:
```bash
DATABASE_URL=postgresql://scraper:password@postgres:5432/unified_scraper
REDIS_URL=redis://redis:6379
CHROMA_HOST=chromadb
CHROMA_PORT=8000
OPENAI_API_KEY=sk-...
```

---

## WORKFLOW

1. **Agent writes code** to GitHub repo (branch or direct to main)
2. **CI/CD runs** on GitHub Actions Ubuntu runners
3. **Podman builds** container images
4. **Tests run** against containerized services
5. **Deploy** to Hetzner VPS (Ubuntu)

---

## RAG & RESEARCH

**GENERAL PURPOSE** - Not just copywriting frameworks.

The system analyzes:
- Authority detection
- Pattern recognition
- Content themes
- Sentiment analysis
- Cross-platform elaboration
- Knowledge extraction

NOT limited to AIDA/PAS/BAB/RMBC frameworks.

---

## OUTPUT FORMAT

All research outputs as **Markdown with YAML frontmatter**:

```markdown
---
id: uuid
platform: twitter
author: dankoe
scraped_at: 2025-11-16T12:00:00Z
---

# Content Title

Body text here...
```

Export path: `/output/{type}/{id}.md`

---

## APPLY TO ALL AGENT PROMPTS

When reading any AGENT_*_PROMPT.md file:
1. **IGNORE** any macOS/homebrew instructions
2. **IGNORE** any local database setup (createdb, psql local)
3. **REPLACE** with containerized equivalents
4. **USE** environment variables for all configuration
5. **ASSUME** Ubuntu server environment

---

## SUMMARY

- **No homebrew** - Ubuntu server
- **No local DB** - Containerized PostgreSQL
- **Use UV** - Not pip
- **Environment vars** - No hardcoded paths
- **Container networking** - Service names, not localhost
- **General research** - Not just copywriting
- **Markdown output** - YAML frontmatter

**If your code requires macOS or local filesystem access, you're doing it wrong.**
