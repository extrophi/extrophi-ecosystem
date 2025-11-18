# Execution Overview - What the CCW Agents Will Actually Do

**Last Updated**: 2025-11-16
**Purpose**: Clear picture of who does what, with what tech stack

---

## Clarification: What Changed in This Session

**You (Claude Desktop - This Instance)** created:
- QA risk assessment document
- User flow diagrams (Mermaid charts)
- Team assignments breakdown
- Package 1 step-by-step guide

**CCW Agents (Claude Code Web)** will execute:
- Package 1: Database setup (PostgreSQL + pgvector)
- Package 2: Twitter scraper (port IAC-024 code)
- Package 3: FastAPI backend
- Package 4: YouTube scraper
- Package 5: Reddit scraper
- Package 6: ChromaDB RAG

**You DID NOT do the user flow mapping implementation** - You documented what it should look like.
**CCW agents WILL implement** the actual scrapers and API based on your docs.

---

## Tech Stack (What They're Building With)

### Backend Core
```
Language: Python 3.11+
Package Manager: uv (per parent CLAUDE.md standards)
Environment: Virtual environment (.venv)
```

### Database (Package 1)
```
Database: PostgreSQL 16
Extension: pgvector (vector similarity search)
ORM: SQLAlchemy 2.0
Migration: Alembic (optional for MVP)
Connection Pool: QueuePool (10 connections, 20 overflow)
```

### Scrapers (Packages 2, 4, 5)

**Twitter (Package 2)**:
```
Primary: Playwright (from IAC-024)
  - persistent_x_session.py (1,231 lines - anti-detection)
  - playwright_oauth_client.py (534 lines - OAuth fallback)
Auth: Username/password + Google OAuth fallback
Anti-detection:
  - Fingerprint spoofing (canvas, WebGL, audio)
  - Human behavior simulation (curved mouse, typing variation)
  - Session health monitoring
  - Intelligent rate limiting
```

**YouTube (Package 4)**:
```
Primary: youtube-transcript-api (instant transcripts)
Fallback: yt-dlp + OpenAI Whisper (when no captions)
Audio: pydub (speed manipulation if needed)
Metadata: yt-dlp (views, likes, upload date)
```

**Reddit (Package 5)**:
```
Library: PRAW (Python Reddit API Wrapper)
Auth: OAuth (client_id, client_secret)
Rate Limit: 1,000 requests / 10 minutes
Endpoints: subreddit.hot(), subreddit.new(), subreddit.search()
```

### Web Scraping (Future - Not MVP)
```
Primary: Jina.ai Reader API (50K pages/month FREE)
  - URL: https://r.jina.ai/{url}
  - Returns: Clean markdown
  - No auth required for free tier

Fallback: ScraperAPI ($49/mo)
  - Complex JS-rendered sites
  - Anti-bot protection
  - Structured endpoints (Amazon, Google SERP)
```

### API Layer (Package 3)
```
Framework: FastAPI 0.109+
ASGI Server: Uvicorn
Async Queue: Redis + RQ (job queue for rate limiting)
Middleware:
  - CORS (allow all origins for MVP)
  - Error handling (proper HTTP status codes)
Docs: Swagger UI (auto-generated at /docs)
```

### RAG/Vector Search (Package 6)
```
Vector DB: ChromaDB (local persistence)
  - Storage: DuckDB + Parquet backend
  - Persist directory: ./data/chromadb (NOT /tmp)
  - Index: HNSW (cosine similarity)

Embeddings: OpenAI text-embedding-3-small
  - Dimensions: 1536
  - Cost: $0.00002 per 1K tokens
  - Batch size: 100 embeddings per request

Similarity: Cosine distance (<=> operator in PostgreSQL, ChromaDB)
```

### LLM Analysis (Future - Not Day 2 MVP)
```
Bulk: OpenAI GPT-3.5 Turbo ($0.0015/1K tokens)
  - Framework extraction
  - Hook identification
  - VOC mining

Polish: Claude Sonnet 4.5 ($3/1M tokens)
  - Final course scripts
  - Copywriting refinement
```

---

## What Each Package Builds

### Package 1: Database Setup (CCW Agent Does This)

**File Structure Created**:
```
backend/
└── db/
    ├── connection.py       # SQLAlchemy engine + session factory
    ├── models.py           # ORM models + Pydantic schemas
    ├── schema.sql          # Raw SQL table definitions
    └── test_vectors.py     # Verification script
```

**Tables Created**:
1. `contents` - Main table (tweets, videos, posts, articles)
   - Columns: platform, source_url, author_id, body, embedding (vector), metrics (JSONB)
   - Indexes: Vector (IVFFlat), platform, author, full-text search (GIN)

2. `authors` - Deduplicated across platforms
   - Columns: canonical_name, twitter_handle, youtube_channel_id, authority_score
   - Indexes: canonical_name

3. `projects` - User research projects
   - Columns: title, topic, platforms, authorities, status

4. `patterns` - Detected elaboration patterns
   - Columns: pattern_type, source_content_id, related_content_ids, similarity scores

**Code Example** (what they'll write):
```python
# backend/db/connection.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://localhost/unified_scraper",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)

def test_connection():
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        print(f"✅ Connected: {result.fetchone()[0]}")
```

**Tests They Run**:
```bash
psql unified_scraper -c "SELECT version();"          # PostgreSQL 16.x
psql unified_scraper -c "\dt"                        # 4 tables
psql unified_scraper -c "\di"                        # 8+ indexes
python -m db.connection                              # Connection test
python -m db.test_vectors                            # Vector similarity
```

---

### Package 2: Twitter Scraper (CCW Agent Does This)

**File Structure Created**:
```
backend/
└── scrapers/
    ├── base.py                       # Abstract BaseScraper class
    └── adapters/
        ├── twitter_core.py           # IAC-024 code (copied, not modified)
        ├── twitter_oauth.py          # OAuth fallback
        └── twitter.py                # Wrapper implementing BaseScraper
```

**Code They Write** (wrapper only):
```python
# backend/scrapers/adapters/twitter.py
from .twitter_core import PersistentXSession  # IAC-024 code
from ..base import BaseScraper
from ...db.models import UnifiedContent

class TwitterScraper(BaseScraper):
    def __init__(self, config):
        # Initialize IAC-024 session (proven code)
        self.session = PersistentXSession(
            profile_dir=config.get('profile_dir', 'data/twitter_profile')
        )

    def extract(self, target: str) -> list:
        """Extract raw tweets using IAC-024 code."""
        return self.session.get_user_tweets(target, limit=100)

    def normalize(self, raw_tweet: dict) -> UnifiedContent:
        """Convert to unified schema."""
        return UnifiedContent(
            platform="twitter",
            source_url=f"https://twitter.com/{raw_tweet['username']}/status/{raw_tweet['id']}",
            external_id=raw_tweet['id'],
            author_id=raw_tweet['user_id'],
            author_name=raw_tweet['username'],
            author_handle=f"@{raw_tweet['username']}",
            content_type='tweet',
            body=raw_tweet['text'],
            published_at=raw_tweet['created_at'],
            metrics={
                'likes': raw_tweet['likes'],
                'retweets': raw_tweet['retweets'],
                'replies': raw_tweet['replies'],
                'views': raw_tweet.get('views', 0)
            }
        )
```

**Code They DON'T Write** (copy from IAC-024):
```python
# backend/scrapers/adapters/twitter_core.py
# This is COPIED EXACTLY from:
# /Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py

class AdvancedFingerprintSpoofing:
    # 200+ lines of anti-bot JavaScript injection
    # DO NOT MODIFY - proven code

class HumanBehaviorSimulator:
    # Curved mouse paths, typing variation, random scrolls
    # DO NOT MODIFY - proven code

class PersistentXSession:
    # Main scraping logic with anti-detection
    # DO NOT MODIFY - proven code
```

**Test They Run**:
```bash
python -c "
from backend.scrapers.adapters.twitter import TwitterScraper
scraper = TwitterScraper({})
tweets = scraper.extract('dankoe')
print(f'✅ Scraped {len(tweets)} tweets')
"
```

---

### Package 3: FastAPI Backend (CCW Agent Does This)

**File Structure Created**:
```
backend/
├── main.py                           # FastAPI app entry
├── api/
│   ├── routes/
│   │   ├── scrape.py                # POST /scrape
│   │   ├── query.py                 # POST /query/rag
│   │   └── generate.py              # POST /generate/course-script
│   └── middleware/
│       ├── cors.py                  # CORS config
│       └── errors.py                # Error handling
└── services/
    ├── scraper_factory.py           # Platform routing
    └── queue.py                     # Redis + RQ jobs
```

**Code They Write**:
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import scrape, query, generate

app = FastAPI(title="Unified Scraper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(scrape.router, prefix="/scrape", tags=["scraping"])
app.include_router(query.router, prefix="/query", tags=["search"])
app.include_router(generate.router, prefix="/generate", tags=["generation"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Unified Scraper API"}

# backend/api/routes/scrape.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.scraper_factory import get_scraper
from services.queue import queue

router = APIRouter()

class ScrapeRequest(BaseModel):
    platform: str  # 'twitter', 'youtube', 'reddit'
    target: str    # '@dankoe', 'video_id', 'r/productivity'
    limit: int = 20

@router.post("/")
async def scrape(request: ScrapeRequest):
    """Universal scraping endpoint."""
    try:
        # Get platform-specific scraper
        scraper = get_scraper(request.platform)

        # Queue scraping job (handles rate limits)
        job = queue.enqueue(
            'scraper_worker',
            scraper.extract,
            request.target,
            request.limit
        )

        return {
            "job_id": job.id,
            "status": "queued",
            "platform": request.platform,
            "target": request.target
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# backend/services/scraper_factory.py
from scrapers.adapters.twitter import TwitterScraper
from scrapers.adapters.youtube import YouTubeScraper
from scrapers.adapters.reddit import RedditScraper

def get_scraper(platform: str):
    """Factory pattern for platform-specific scrapers."""
    scrapers = {
        "twitter": TwitterScraper,
        "youtube": YouTubeScraper,
        "reddit": RedditScraper
    }

    if platform not in scrapers:
        raise ValueError(f"Platform '{platform}' not supported")

    return scrapers[platform](config={})
```

**Test They Run**:
```bash
# Start server
uvicorn backend.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"platform": "twitter", "target": "dankoe", "limit": 10}'

# Check Swagger docs
open http://localhost:8000/docs
```

---

### Package 4: YouTube Scraper (CCW Agent Does This)

**File Structure Created**:
```
backend/
└── scrapers/
    └── adapters/
        ├── youtube.py                # Main scraper
        └── youtube_whisper.py        # Fallback transcription
```

**Code They Write**:
```python
# backend/scrapers/adapters/youtube.py
from youtube_transcript_api import YouTubeTranscriptApi
from ..base import BaseScraper
from ...db.models import UnifiedContent
from .youtube_whisper import whisper_transcribe
import yt_dlp

class YouTubeScraper(BaseScraper):
    def extract(self, video_id: str) -> dict:
        """Extract video metadata and transcript."""
        # Get metadata
        ydl = yt_dlp.YoutubeDL({'quiet': True})
        info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}", download=False)

        # Try transcript API first (instant)
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = ' '.join([t['text'] for t in transcript])
        except:
            # Fallback to Whisper (2 min/video)
            transcript_text = whisper_transcribe(video_id)

        return {
            'video_id': video_id,
            'title': info['title'],
            'channel_name': info['channel'],
            'channel_id': info['channel_id'],
            'upload_date': info['upload_date'],
            'view_count': info['view_count'],
            'like_count': info.get('like_count', 0),
            'transcript': transcript_text
        }

    def normalize(self, raw_data: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="youtube",
            source_url=f"https://youtube.com/watch?v={raw_data['video_id']}",
            external_id=raw_data['video_id'],
            author_id=raw_data['channel_id'],
            author_name=raw_data['channel_name'],
            content_type='video',
            title=raw_data['title'],
            body=raw_data['transcript'],
            metrics={
                'views': raw_data['view_count'],
                'likes': raw_data['like_count']
            }
        )

# backend/scrapers/adapters/youtube_whisper.py
import whisper
import yt_dlp

def whisper_transcribe(video_id: str) -> str:
    """Fallback transcription using Whisper."""
    # Download audio
    ydl_opts = {'format': 'bestaudio', 'outtmpl': f'temp_{video_id}.wav'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://youtube.com/watch?v={video_id}"])

    # Transcribe with Whisper
    model = whisper.load_model("base")
    result = model.transcribe(f"temp_{video_id}.wav")

    return result["text"]
```

**Dependencies They Install**:
```bash
uv pip install youtube-transcript-api yt-dlp openai-whisper
```

---

### Package 5: Reddit Scraper (CCW Agent Does This)

**File Structure Created**:
```
backend/
└── scrapers/
    └── adapters/
        └── reddit.py                 # PRAW scraper
```

**Code They Write**:
```python
# backend/scrapers/adapters/reddit.py
import praw
import os
from ..base import BaseScraper
from ...db.models import UnifiedContent

class RedditScraper(BaseScraper):
    def __init__(self, config):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="Unified Scraper 1.0"
        )

    def extract(self, subreddit_name: str, limit: int = 50) -> list:
        """Scrape posts from subreddit."""
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        for post in subreddit.hot(limit=limit):
            posts.append({
                'id': post.id,
                'title': post.title,
                'body': post.selftext,
                'author': post.author.name if post.author else '[deleted]',
                'subreddit': subreddit_name,
                'upvotes': post.score,
                'comments': post.num_comments,
                'created_utc': post.created_utc,
                'url': f"https://reddit.com{post.permalink}"
            })

        return posts

    def normalize(self, raw_post: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="reddit",
            source_url=raw_post['url'],
            external_id=raw_post['id'],
            author_id=raw_post['author'],
            author_name=raw_post['author'],
            content_type='post',
            title=raw_post['title'],
            body=raw_post['body'],
            metrics={
                'upvotes': raw_post['upvotes'],
                'comments': raw_post['comments']
            }
        )
```

**Setup They Document**:
```bash
# User needs to create Reddit app at https://reddit.com/prefs/apps
# Then set environment variables:
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_secret"
```

---

### Package 6: ChromaDB RAG (CCW Agent Does This)

**File Structure Created**:
```
backend/
└── services/
    ├── embeddings.py                 # OpenAI embedding generation
    ├── chromadb_client.py            # ChromaDB setup
    └── rag_query.py                  # Semantic search
```

**Code They Write**:
```python
# backend/services/chromadb_client.py
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/chromadb"  # Persistent storage
))

collection = client.get_or_create_collection(
    name="unified_content",
    metadata={"hnsw:space": "cosine"}
)

# backend/services/embeddings.py
from openai import OpenAI
import os

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text: str) -> list[float]:
    """Generate 1536-dim embedding."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def batch_embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings in batches of 100."""
    embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i:i+100]
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        embeddings.extend([d.embedding for d in response.data])
    return embeddings

# backend/services/rag_query.py
from .chromadb_client import collection
from .embeddings import generate_embedding

def semantic_search(query: str, limit: int = 20, filters: dict = None):
    """Search content by semantic similarity."""
    query_embedding = generate_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=filters  # e.g., {"platform": "twitter"}
    )

    return results
```

**Test They Run**:
```python
from services.rag_query import semantic_search

# Index test content
collection.add(
    documents=["Focus is the new currency"],
    ids=["test-1"]
)

# Search
results = semantic_search("focus systems", limit=5)
print(f"✅ Found {len(results['documents'])} results")
```

---

## Timeline (What Happens When)

### T+0: Package 1 Starts (1 CCW agent)
```
Hour 0-1: PostgreSQL installation
Hour 1-2: Schema creation, connection testing
Output: Database ready ✅
```

### T+2: Packages 2-6 Start (5 CCW agents parallel)
```
Agent 1 (Twitter):   Hours 2-5 (3h)
Agent 2 (API):       Hours 2-4 (2h)
Agent 3 (YouTube):   Hours 2-4 (2h)
Agent 4 (Reddit):    Hours 2-3 (1h)
Agent 5 (ChromaDB):  Hours 2-4 (2h)

All complete by Hour 5-6
```

### T+6: Integration (Agent 2 continues)
```
Hour 6-7: Connect all scrapers to API
Hour 7: Test end-to-end
Output: MVP ready ✅
```

---

## What YOU Did (This Session)

**Research & Documentation** (not implementation):
1. ✅ Analyzed yt-agent-app for YouTube patterns
2. ✅ Researched GitHub scrapers (Twitter, Reddit, Amazon)
3. ✅ QA risk assessment (10 failure points)
4. ✅ User flow diagrams (Mermaid charts)
5. ✅ Team assignments (6 packages breakdown)
6. ✅ Package 1 step-by-step guide (724 lines)
7. ✅ Updated CLAUDE.md with hybrid stack decision

**You did NOT**:
- ❌ Install PostgreSQL
- ❌ Write scraper code
- ❌ Set up FastAPI
- ❌ Implement user flow

**CCW agents WILL**:
- ✅ Execute all 6 packages (actual coding)
- ✅ Install dependencies
- ✅ Test and verify
- ✅ Commit code

---

## Summary: The Plan

**Tech Stack**:
- Database: PostgreSQL 16 + pgvector
- Backend: FastAPI + SQLAlchemy
- Queue: Redis + RQ
- Scrapers: Playwright (Twitter), yt-dlp (YouTube), PRAW (Reddit)
- RAG: ChromaDB + OpenAI embeddings
- Cost: $20-89/mo (vs competitors $49-299/mo)

**Execution**:
- Package 1 first (1-2h) - Database foundation
- Packages 2-6 parallel (4h) - All scrapers + API
- Integration (1h) - End-to-end testing
- **Total: 6-7 hours to MVP**

**Your role**: Technical lead (document, research, command)
**CCW agents role**: Developers (execute, code, test)

**Next**: Spawn Package 1 CCW agent with PACKAGE_1_DATABASE_SETUP.md as prompt.
