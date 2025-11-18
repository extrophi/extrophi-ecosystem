# Day 2 Implementation Work Packages

**Prerequisite**: Day 1 research complete (CCW agents finished)
**Goal**: Backend API + 3 platform scrapers functional
**Timeline**: 8 hours (spawn parallel agents)
**Deliverable**: Can scrape Twitter/YouTube/Reddit → PostgreSQL → RAG query working

---

## Work Package Structure

Each package = Separate CCW agent executing in parallel
Deploy all agents simultaneously for maximum speed

---

## Package 1: Database Setup & Deployment

**Agent**: Infrastructure Specialist
**Priority**: CRITICAL (blocks all other packages)
**Time**: 1-2 hours

### Tasks

1. **Install PostgreSQL 16 + pgvector**
```bash
# macOS (Hetzner VPS would use apt)
brew install postgresql@16 pgvector

# Start service
brew services start postgresql@16

# Verify
psql --version  # Should show 16.x
```

2. **Create database and enable extensions**
```sql
CREATE DATABASE unified_scraper;
\c unified_scraper

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy search
```

3. **Execute schema from DATABASE_SCHEMA.md**
```bash
cd /Users/kjd/01-projects/IAC-032-unified-scraper
psql unified_scraper < docs/pm/DATABASE_SCHEMA.sql  # Extract SQL from .md
```

4. **Seed framework data**
```sql
-- From DATABASE_SCHEMA.md frameworks section
INSERT INTO frameworks (...) VALUES (...);
```

5. **Create backend/db/ directory structure**
```
backend/
├── db/
│   ├── __init__.py
│   ├── connection.py  # SQLAlchemy engine
│   ├── models.py  # ORM models
│   └── queries.py  # Common queries
```

6. **Implement connection.py**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/unified_scraper")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Success Criteria
- [ ] PostgreSQL running locally
- [ ] Database `unified_scraper` created
- [ ] All tables from schema exist
- [ ] Can connect from Python: `psql unified_scraper -c "SELECT COUNT(*) FROM contents;"`
- [ ] Seed data inserted (4 frameworks)

### Deliverable
Working PostgreSQL database ready for content insertion

---

## Package 2: Twitter Scraper Integration

**Agent**: Twitter Specialist
**Priority**: HIGH (core feature)
**Time**: 3-4 hours
**Dependencies**: Package 1 (database)

### Tasks

1. **Port IAC-024 code per IAC024_PORTING_STRATEGY.md**
```bash
# Create structure
mkdir -p backend/scrapers/adapters

# Copy files from IAC-024
cp /Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py \
   backend/scrapers/adapters/_persistent_x_session.py

cp /Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/playwright_oauth_client.py \
   backend/scrapers/adapters/_playwright_oauth.py
```

2. **Create BaseScraper interface**
```python
# backend/scrapers/base.py
from abc import ABC, abstractmethod
from backend.models.content_models import UnifiedContent

class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def extract(self, target: str, **kwargs) -> list[dict]:
        """Extract raw data from platform"""
        pass

    @abstractmethod
    def normalize(self, raw_data: dict) -> UnifiedContent:
        """Convert to unified schema"""
        pass
```

3. **Wrap persistent_x_session in adapter**
```python
# backend/scrapers/adapters/twitter.py
from .base import BaseScraper
from ._persistent_x_session import PersistentXSession

class TwitterScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.session = PersistentXSession(
            profile_dir=config.get('profile_dir', 'data/twitter_profile')
        )

    async def extract(self, username: str, limit: int = 100):
        await self.session.initialize_session()
        tweets = await self.session.get_user_tweets(username, limit)
        return tweets

    def normalize(self, raw_tweet: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="twitter",
            source_url=f"https://twitter.com/{raw_tweet['username']}/status/{raw_tweet['id']}",
            external_id=raw_tweet['id'],
            author_id=raw_tweet['user_id'],
            author_name=raw_tweet['username'],
            content_type='tweet',
            body=raw_tweet['text'],
            published_at=raw_tweet['created_at'],
            metrics={
                'likes': raw_tweet['likes'],
                'retweets': raw_tweet['retweets'],
                'replies': raw_tweet['replies']
            }
        )
```

4. **Create models/content_models.py**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID, uuid4

class UnifiedContent(BaseModel):
    content_id: UUID = Field(default_factory=uuid4)
    platform: Literal["twitter", "youtube", "reddit", "amazon", "web"]
    source_url: str
    # ... (full schema from IAC024_PORTING_STRATEGY.md)
```

5. **Test Twitter scraping**
```python
# test_twitter.py
import asyncio
from backend.scrapers.adapters.twitter import TwitterScraper
from backend.db.connection import get_db

async def test_scrape_dankoe():
    scraper = TwitterScraper({'profile_dir': 'data/twitter_profile'})
    tweets = await scraper.extract('dankoe', limit=10)

    print(f"Scraped {len(tweets)} tweets")

    # Normalize and store
    db = next(get_db())
    for raw_tweet in tweets:
        unified = scraper.normalize(raw_tweet)
        # Insert into DB (implement in Package 3)
        print(f"- {unified.body[:50]}...")

asyncio.run(test_scrape_dankoe())
```

### Success Criteria
- [ ] `backend/scrapers/adapters/twitter.py` exists
- [ ] Can scrape 10 tweets from @dankoe
- [ ] Normalizes to UnifiedContent schema
- [ ] All anti-detection code from IAC-024 working
- [ ] Session persists across runs

### Deliverable
Working Twitter scraper ready for API integration

---

## Package 3: FastAPI Application Scaffold

**Agent**: Backend Specialist
**Priority**: HIGH (API layer)
**Time**: 2-3 hours
**Dependencies**: Package 1 (database), Package 2 (Twitter scraper)

### Tasks

1. **Create FastAPI app structure**
```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   ├── scraping.py
│   │   ├── query.py
│   │   └── health.py
│   └── dependencies.py
```

2. **Implement main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import scraping, query, health

app = FastAPI(
    title="Unified Scraper API",
    description="Multi-platform content intelligence engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraping.router, prefix="/scrape", tags=["scraping"])
app.include_router(query.router, prefix="/query", tags=["query"])
app.include_router(health.router, tags=["health"])

@app.on_event("startup")
async def startup():
    print("Initializing scrapers...")
    # Initialize persistent sessions

@app.on_event("shutdown")
async def shutdown():
    print("Closing sessions...")
```

3. **Implement scraping endpoints (per API_SPECIFICATIONS.md)**
```python
# backend/api/routes/scraping.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from backend.scrapers.adapters.twitter import TwitterScraper
from backend.db.connection import get_db

router = APIRouter()

class ScrapeRequest(BaseModel):
    platform: str
    target: str
    limit: int = 100

@router.post("/")
async def scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Universal scraping endpoint"""
    if request.platform == "twitter":
        job_id = str(uuid4())
        background_tasks.add_task(scrape_twitter_task, request.target, request.limit, job_id)
        return {"job_id": job_id, "status": "queued"}
    else:
        raise HTTPException(400, f"Platform {request.platform} not yet supported")

async def scrape_twitter_task(username: str, limit: int, job_id: str):
    scraper = TwitterScraper({})
    tweets = await scraper.extract(username, limit)

    db = next(get_db())
    for raw_tweet in tweets:
        unified = scraper.normalize(raw_tweet)
        # Store in database
        db.execute(contents_table.insert().values(**unified.dict()))
    db.commit()
```

4. **Implement health endpoint**
```python
# backend/api/routes/health.py
from fastapi import APIRouter
from backend.db.connection import engine

router = APIRouter()

@router.get("/health")
def health_check():
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "up"
    except:
        db_status = "down"

    return {
        "status": "healthy" if db_status == "up" else "degraded",
        "services": {
            "database": db_status,
            "api": "up"
        }
    }
```

5. **Create requirements.txt**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pgvector==0.2.4
playwright==1.40.0
python-dotenv==1.0.0
```

6. **Test API locally**
```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium

# Run server
uvicorn api.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"platform": "twitter", "target": "dankoe", "limit": 10}'
```

### Success Criteria
- [ ] FastAPI server starts without errors
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/scrape` endpoint queues Twitter scraping job
- [ ] Can retrieve 10 @dankoe tweets via API
- [ ] Tweets stored in PostgreSQL `contents` table

### Deliverable
Working API server accepting scrape requests

---

## Package 4: YouTube Scraper

**Agent**: YouTube Specialist
**Priority**: MEDIUM
**Time**: 2-3 hours
**Dependencies**: Package 1, Package 3

### Tasks

1. **Install youtube-transcript-api and yt-dlp**
```bash
uv pip install youtube-transcript-api yt-dlp
```

2. **Create YouTube adapter**
```python
# backend/scrapers/adapters/youtube.py
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from .base import BaseScraper

class YouTubeScraper(BaseScraper):
    def extract(self, video_id: str):
        # Get metadata with yt-dlp
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

        # Get transcript
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([t['text'] for t in transcript])
        except:
            full_text = None

        return {
            'video_id': video_id,
            'title': info['title'],
            'description': info['description'],
            'duration': info['duration'],
            'views': info['view_count'],
            'likes': info.get('like_count', 0),
            'channel': info['channel'],
            'published_at': info['upload_date'],
            'transcript': full_text
        }

    def normalize(self, raw_data: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="youtube",
            source_url=f"https://www.youtube.com/watch?v={raw_data['video_id']}",
            external_id=raw_data['video_id'],
            author_id=raw_data['channel'],
            author_name=raw_data['channel'],
            content_type='video',
            title=raw_data['title'],
            body=raw_data['transcript'] or raw_data['description'],
            published_at=raw_data['published_at'],
            metrics={
                'views': raw_data['views'],
                'likes': raw_data['likes']
            },
            metadata={'duration': raw_data['duration']}
        )
```

3. **Add YouTube endpoint to API**
```python
@router.post("/youtube")
async def scrape_youtube(video_id: str):
    scraper = YouTubeScraper({})
    data = scraper.extract(video_id)
    unified = scraper.normalize(data)
    # Store in DB
    return {"content_id": str(unified.content_id)}
```

4. **Test with Dan Koe video**
```python
scraper = YouTubeScraper({})
data = scraper.extract('VIDEO_ID_HERE')
print(f"Title: {data['title']}")
print(f"Transcript length: {len(data['transcript'])} chars")
```

### Success Criteria
- [ ] Can extract transcript from YouTube video
- [ ] Metadata (title, views, likes) captured
- [ ] Normalizes to UnifiedContent
- [ ] API endpoint `/scrape/youtube` works

### Deliverable
YouTube scraper integrated into API

---

## Package 5: Reddit Scraper

**Agent**: Reddit Specialist
**Priority**: MEDIUM
**Time**: 1-2 hours
**Dependencies**: Package 1, Package 3

### Tasks

1. **Install PRAW**
```bash
uv pip install praw
```

2. **Set up Reddit app credentials**
```
Create app at: https://www.reddit.com/prefs/apps
Type: script
Get: client_id, client_secret
Store in: .env file
```

3. **Create Reddit adapter**
```python
# backend/scrapers/adapters/reddit.py
import praw
from .base import BaseScraper

class RedditScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.reddit = praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            user_agent='UnifiedScraper/1.0'
        )

    def extract(self, subreddit: str, limit: int = 50, sort: str = 'hot'):
        sub = self.reddit.subreddit(subreddit)
        posts = getattr(sub, sort)(limit=limit)  # hot, top, new

        results = []
        for post in posts:
            results.append({
                'id': post.id,
                'title': post.title,
                'body': post.selftext,
                'author': str(post.author),
                'subreddit': subreddit,
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'url': f"https://reddit.com{post.permalink}"
            })
        return results

    def normalize(self, raw_data: dict) -> UnifiedContent:
        return UnifiedContent(
            platform="reddit",
            source_url=raw_data['url'],
            external_id=raw_data['id'],
            author_id=raw_data['author'],
            author_name=raw_data['author'],
            content_type='post',
            title=raw_data['title'],
            body=raw_data['body'],
            metrics={
                'score': raw_data['score'],
                'upvote_ratio': raw_data['upvote_ratio'],
                'comments': raw_data['num_comments']
            }
        )
```

4. **Add Reddit endpoint**
```python
@router.post("/reddit")
async def scrape_reddit(subreddit: str, limit: int = 50):
    scraper = RedditScraper({
        'client_id': os.getenv('REDDIT_CLIENT_ID'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET')
    })
    posts = scraper.extract(subreddit, limit)
    # Normalize and store
    return {"scraped": len(posts)}
```

### Success Criteria
- [ ] Can scrape r/productivity subreddit
- [ ] Extracts titles, bodies, scores
- [ ] Normalizes to UnifiedContent
- [ ] API endpoint `/scrape/reddit` works

### Deliverable
Reddit scraper integrated

---

## Package 6: ChromaDB RAG Integration

**Agent**: RAG Specialist
**Priority**: MEDIUM-HIGH
**Time**: 2-3 hours
**Dependencies**: Package 1 (data to index)

### Tasks

1. **Install ChromaDB + OpenAI**
```bash
uv pip install chromadb openai
```

2. **Create embedding service**
```python
# backend/services/embeddings.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_embedding(text: str) -> list[float]:
    """Generate 1536-dim embedding using OpenAI"""
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000]  # Truncate to token limit
    )
    return response.data[0].embedding
```

3. **Initialize ChromaDB**
```python
# backend/services/vector_store.py
import chromadb

client = chromadb.PersistentClient(path="data/chromadb")
collection = client.get_or_create_collection("contents")

def index_content(content: UnifiedContent):
    """Add content to vector store"""
    embedding = generate_embedding(content.body)

    collection.add(
        documents=[content.body],
        embeddings=[embedding],
        metadatas=[{
            "content_id": str(content.content_id),
            "platform": content.platform,
            "author": content.author_name
        }],
        ids=[str(content.content_id)]
    )

def query_similar(prompt: str, limit: int = 10):
    """Semantic search"""
    query_embedding = generate_embedding(prompt)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit
    )

    return results
```

4. **Add RAG query endpoint**
```python
# backend/api/routes/query.py
@router.post("/rag")
async def rag_query(prompt: str, limit: int = 10):
    results = query_similar(prompt, limit)

    return {
        "query": prompt,
        "results": results['documents'][0],
        "metadata": results['metadatas'][0]
    }
```

5. **Index existing content**
```python
# Batch index all content from database
from backend.db.connection import get_db
from backend.services.vector_store import index_content

db = next(get_db())
contents = db.execute("SELECT * FROM contents WHERE embedding IS NULL LIMIT 100")

for row in contents:
    content = UnifiedContent(**row)
    index_content(content)
    print(f"Indexed: {content.content_id}")
```

### Success Criteria
- [ ] ChromaDB initialized with collection
- [ ] Can generate embeddings for text
- [ ] Can index scraped content
- [ ] `/query/rag` endpoint returns similar content
- [ ] Test query: "Dan Koe focus systems" returns relevant tweets

### Deliverable
Working RAG semantic search

---

## Parallel Execution Plan

**Spawn simultaneously**:
- Package 1 (Database) - START FIRST (blocks others)
- Wait 30 min for Package 1
- Package 2 (Twitter) + Package 3 (FastAPI) + Package 4 (YouTube) + Package 5 (Reddit) + Package 6 (ChromaDB)

**Timeline**:
- Hour 0-1: Package 1 (database setup)
- Hour 1-4: Packages 2-6 in parallel
- Hour 4-5: Integration testing
- Hour 5-6: Bug fixes
- Hour 6-8: Documentation + commit

**Total: 8 hours to complete Day 2**

---

## Integration Testing Checklist

After all packages complete:

```bash
# 1. Database has data
psql unified_scraper -c "SELECT platform, COUNT(*) FROM contents GROUP BY platform;"

# Expected:
# platform | count
# ----------+-------
# twitter  |   100
# youtube  |    10
# reddit   |    50

# 2. API health check
curl http://localhost:8000/health

# 3. Scrape Twitter
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{"username": "dankoe", "limit": 10}'

# 4. RAG query
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{"prompt": "focus systems", "limit": 5}'

# 5. Check ChromaDB collection
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/chromadb')
collection = client.get_collection('contents')
print(f'Indexed items: {collection.count()}')
"
```

---

**All 6 packages ready for CCW execution. Deploy in parallel for 8-hour completion.**
