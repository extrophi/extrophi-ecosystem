# CCW Day 2 Sprint - Fix Errors + Complete Build

**PRIORITY 1: Fix CI failures, then build remaining features**

---

## PART 1: FIX MYPY ERRORS (14 errors, 5 files)

### 1. backend/tests/conftest.py:18
```python
# CHANGE:
def mock_db_session() -> MagicMock:
    yield session

# TO:
from typing import Generator
def mock_db_session() -> Generator[MagicMock, None, None]:
    yield session
```

### 2. backend/db/models.py (lines 21, 70, 110, 137)
```python
# CHANGE line 13:
Base = declarative_base()

# TO:
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 3. backend/scrapers/adapters/twitter.py:52
```python
# CHANGE line 52:
tweets = []

# TO:
tweets: list[dict[str, Any]] = []

# Also fix line 115 - comments is not a MetricsModel field:
# CHANGE:
comments=raw_data["public_metrics"].get("reply_count", 0),

# TO:
replies=raw_data["public_metrics"].get("reply_count", 0),
```

### 4. backend/api/routes/analyze.py:46
```python
# CHANGE:
content_list = []

# TO:
content_list: list[dict[str, Any]] = []
```

### 5. backend/queue/tasks.py (lines 11, 50, 79)
Add return statements after retry calls:
```python
# After each self.retry() call, add:
return {"status": "retrying", "error": str(exc)}
```

---

## PART 2: BUILD REMAINING FEATURES

### ChromaDB Vector Store
Create `backend/vector/chromadb_client.py`:
```python
"""ChromaDB client for semantic search."""

import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "chromadb"),
            port=int(os.getenv("CHROMA_PORT", "8000")),
        )
        self.collection = self.client.get_or_create_collection("content")

    def add(self, id: str, embedding: list[float], metadata: dict):
        self.collection.add(ids=[id], embeddings=[embedding], metadatas=[metadata])

    def query(self, embedding: list[float], n_results: int = 10):
        return self.collection.query(query_embeddings=[embedding], n_results=n_results)
```

### RAG Query Endpoint
Create `backend/api/routes/query.py`:
```python
from fastapi import APIRouter
from backend.vector.chromadb_client import VectorStore

router = APIRouter(prefix="/query", tags=["query"])

@router.post("/rag")
async def rag_query(prompt: str, limit: int = 10):
    # Generate embedding for prompt
    # Query ChromaDB for similar content
    # Return results with citations
    pass
```

### Course Script Generator
Create `backend/api/routes/generate.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/generate", tags=["generate"])

@router.post("/course-script")
async def generate_course_script(brief: dict):
    # Parse project brief
    # Query RAG for relevant content
    # Generate script with LLM
    # Include citations
    pass
```

---

## PART 3: DEPLOYMENT FILES

### Podman Compose
Update `deployment/podman-compose.yaml` with all services:
- FastAPI backend (port 8000)
- PostgreSQL + pgvector
- Redis
- ChromaDB
- Celery worker

### Environment Template
Create `.env.example`:
```
DATABASE_URL=postgresql://user:pass@postgres:5432/scraper
REDIS_URL=redis://redis:6379/0
CHROMA_HOST=chromadb
CHROMA_PORT=8000
OPENAI_API_KEY=your-key-here
```

---

## COMMANDS

```bash
# 1. Fix all MyPy errors
# Edit the files as shown above

# 2. Verify lint passes
black backend/
isort backend/
ruff check backend/ --fix
mypy --ignore-missing-imports backend/

# 3. Run tests
pytest tests/unit/ -v

# 4. Commit and push
git add -A
git commit -m "fix: All MyPy errors + add ChromaDB, RAG, deployment configs"
git push origin main
```

---

## SUCCESS CRITERIA

- [ ] CI passes (all MyPy errors fixed)
- [ ] ChromaDB client working
- [ ] RAG query endpoint functional
- [ ] Course script generator endpoint exists
- [ ] Podman compose ready for Hetzner
- [ ] All tests passing

GO.
