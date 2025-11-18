# DOCUMENTATION DOWNLOAD & CONVERSION PLAN
## Essential Before Sub-Agents Start Work

**Purpose:** Sub-agents need current docs to write flawless code

---

## EXISTING TOOL

```
Location: /Users/kjd/01-projects/IAC-033-extrophi-ecosystem/research/tools/doc-scraper/
Purpose: Converts HTML docs → Markdown
Technology: Python (already set up)
```

---

## DOCUMENTATION STRUCTURE

```
IAC-033-extrophi-ecosystem/
├── dev/                    (ROOT LEVEL - orchestrator docs)
│   ├── fastapi/
│   ├── postgresql/
│   ├── uvicorn/
│   └── python-best-practices/
│
├── writer/
│   └── dev/               (WRITER-SPECIFIC docs)
│       ├── tauri-v2/      (Latest - Tauri 2)
│       ├── svelte-v5/     (Latest - Svelte 5)
│       ├── rust/
│       ├── typescript/
│       └── sqlite/
│
├── research/
│   └── dev/               (RESEARCH-SPECIFIC docs)
│       ├── fastapi/
│       ├── playwright/
│       ├── beautifulsoup/
│       ├── postgresql/
│       └── pgvector/
│
└── backend/
    └── dev/               (BACKEND-SPECIFIC docs)
        ├── fastapi/
        ├── postgresql/
        ├── sqlalchemy/
        └── pydantic/
```

---

## CRITICAL VERSIONS

**Writer Module:**
- ✅ Tauri 2 (latest)
- ✅ Svelte 5 (latest)
- Rust (latest stable)
- TypeScript 5.x
- SQLite 3.x

**Research Module:**
- FastAPI 0.109+
- Playwright (latest)
- PostgreSQL 15+
- pgvector 0.5+

**Backend Module:**
- FastAPI 0.109+
- PostgreSQL 15+
- SQLAlchemy 2.x
- Pydantic v2

**DO NOT use Docker - use Podman**
- Docker has commercial licensing
- Podman is free, compatible
- Already decided in previous sessions

---

## DOCUMENTATION SOURCES

### Writer:
```
Tauri 2: https://v2.tauri.app/start/
Svelte 5: https://svelte.dev/docs/svelte/overview
Rust: https://doc.rust-lang.org/book/
TypeScript: https://www.typescriptlang.org/docs/
SQLite: https://www.sqlite.org/docs.html
```

### Research:
```
FastAPI: https://fastapi.tiangolo.com/
Playwright: https://playwright.dev/python/docs/intro
PostgreSQL: https://www.postgresql.org/docs/15/
pgvector: https://github.com/pgvector/pgvector#readme
```

### Backend:
```
FastAPI: https://fastapi.tiangolo.com/
SQLAlchemy: https://docs.sqlalchemy.org/en/20/
Pydantic: https://docs.pydantic.dev/latest/
```

### Orchestrator (Root):
```
Podman: https://docs.podman.io/en/latest/
Docker Compose → Podman Compose: https://github.com/containers/podman-compose
Nginx: https://nginx.org/en/docs/
```

---

## CONVERSION PROCESS

### Step 1: Download HTML
```bash
cd /Users/kjd/01-projects/IAC-033-extrophi-ecosystem/research/tools/doc-scraper

# Example: Download Tauri 2 docs
python scrape_docs.py --url https://v2.tauri.app/start/ \
  --output ../../writer/dev/tauri-v2/ \
  --format markdown
```

### Step 2: Organize
```bash
# Move to correct dev/ folder
# Ensure structure: dev/technology-name/page-name.md
```

### Step 3: Commit
```bash
git add dev/
git commit -m "docs: Add [technology] documentation for [module]"
git push
```

### Step 4: Sub-agents can access
- Documentation in GitHub
- Sub-agents read from dev/ folders
- Up-to-date, accurate info

---

## ROOT CCL TASK SEQUENCE

**BEFORE spawning any coding sub-agents:**

1. ✅ Execute cleanup (files in correct places)
2. ✅ Download documentation (using doc-scraper)
3. ✅ Convert to markdown
4. ✅ Organize in dev/ folders
5. ✅ Commit to GitHub
6. ✅ THEN spawn coding sub-agents

**Time estimate:** 45-60 minutes total prep work

---

## WHY THIS MATTERS

**Without docs:**
- Sub-agents use training data (outdated)
- May use wrong API versions
- Code breaks, wasted time

**With docs:**
- Sub-agents read current, correct docs
- Use exact versions we specify
- Code works first time
- Flawless implementation

---

## DOC-SCRAPER TOOL SETUP

```bash
cd research/tools/doc-scraper

# Check if dependencies installed
ls .venv/

# If not:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Test
python scrape_docs.py --help
```

---

## AUTOMATED SCRIPT

```bash
#!/bin/bash
# download-all-docs.sh

set -e

cd /Users/kjd/01-projects/IAC-033-extrophi-ecosystem/research/tools/doc-scraper
source .venv/bin/activate

echo "=== Downloading Writer docs ==="
python scrape_docs.py --url https://v2.tauri.app/start/ \
  --output ../../writer/dev/tauri-v2/ --format markdown

python scrape_docs.py --url https://svelte.dev/docs/svelte/overview \
  --output ../../writer/dev/svelte-v5/ --format markdown

echo "=== Downloading Research docs ==="
python scrape_docs.py --url https://fastapi.tiangolo.com/ \
  --output ../../research/dev/fastapi/ --format markdown

python scrape_docs.py --url https://playwright.dev/python/docs/intro \
  --output ../../research/dev/playwright/ --format markdown

echo "=== Downloading Backend docs ==="
python scrape_docs.py --url https://docs.sqlalchemy.org/en/20/ \
  --output ../../backend/dev/sqlalchemy/ --format markdown

echo "=== Downloading Orchestrator docs ==="
python scrape_docs.py --url https://docs.podman.io/en/latest/ \
  --output ../../dev/podman/ --format markdown

echo "=== Complete ==="
cd ../../../
git add dev/ writer/dev/ research/dev/ backend/dev/
git commit -m "docs: Download and convert all module documentation"
git push
```

---

## ROOT CCL EXECUTION

```
Task 1: Cleanup (30 min)
→ WAIT for approval

Task 2: Documentation (45 min)
→ Run download-all-docs.sh
→ Verify markdown files created
→ Commit to GitHub
→ WAIT for approval

Task 3: Spawn sub-agents
→ Sub-agents now have docs
→ Begin coding work
```

---

**CRITICAL:** Documentation BEFORE coding  
**INVESTMENT:** 45 minutes saves hours of debugging  
**RESULT:** Flawless code using correct versions
