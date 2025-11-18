# Parallel Team Assignments - Let's Build This Thing

**Updated**: 2025-11-16
**Strategy**: Carve up the work, spawn CCW agents, ship fast

---

## Team Structure (6 Parallel Agents)

### Team 1: Database Engineer (CRITICAL - GOES FIRST)
### Team 2: Twitter Scraper Specialist
### Team 3: Backend API Engineer
### Team 4: YouTube Scraper Specialist
### Team 5: Reddit Scraper Specialist
### Team 6: RAG/ChromaDB Engineer

---

## 🔴 TEAM 1: Database Engineer (Package 1 - CRITICAL FIRST)

**Duration**: 1-2 hours
**Blocks**: Teams 2-6 (they all need the database)
**Risk**: HIGH - If this fails, everything fails

### Objective
Set up PostgreSQL with pgvector extension and create unified content schema.

### Deliverables
```
backend/db/
├── connection.py      # SQLAlchemy connection pooling
├── models.py          # Pydantic + SQLAlchemy models
├── schema.sql         # Table definitions
└── migrations/        # Alembic migrations
    └── 001_initial.sql
```

### Tasks
1. **Install PostgreSQL 16 + pgvector**
   ```bash
   brew install postgresql@16 pgvector
   brew services start postgresql@16
   createdb unified_scraper
   psql unified_scraper -c "CREATE EXTENSION vector;"
   ```

2. **Create tables from DATABASE_SCHEMA.md**
   - `contents` (main table with vector column)
   - `authors` (author metadata)
   - `projects` (user research projects)
   - `patterns` (detected elaboration patterns)

3. **Create indexes**
   ```sql
   CREATE INDEX idx_contents_embedding ON contents
   USING ivfflat (embedding vector_cosine_ops);

   CREATE INDEX idx_contents_platform ON contents(platform);
   CREATE INDEX idx_contents_author ON contents(author_id);
   CREATE INDEX idx_contents_fts ON contents
   USING GIN(to_tsvector('english', content_body));
   ```

4. **Implement connection.py**
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool

   engine = create_engine(
       "postgresql://localhost/unified_scraper",
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=20
   )
   ```

5. **Test vector similarity**
   ```sql
   SELECT content_id,
          1 - (embedding <=> '[0.1, 0.2, ...]') as similarity
   FROM contents
   ORDER BY embedding <=> '[0.1, 0.2, ...]'
   LIMIT 10;
   ```

### Success Criteria
- [ ] `psql unified_scraper -c "SELECT version();"` works
- [ ] Vector index created and tested
- [ ] Can insert 100 test rows in <1 second
- [ ] Similarity search returns in <500ms

### Reference Docs
- `docs/pm/DATABASE_SCHEMA.md` (600 lines - complete schema)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 1 section)

### Commit Message Template
```
feat(db): Setup PostgreSQL with pgvector

- Install PostgreSQL 16 + pgvector extension
- Create unified_scraper database
- Implement SQLAlchemy models with vector support
- Add connection pooling (max 10 connections)
- Test vector similarity search (<=> operator)

Tables: contents, authors, projects, patterns
Indexes: vector (ivfflat), platform, author_id, FTS

Ref: docs/pm/DATABASE_SCHEMA.md, Package 1
```

---

## 🟦 TEAM 2: Twitter Scraper Specialist (Package 2)

**Duration**: 3-4 hours
**Depends on**: Team 1 (database)
**Risk**: HIGH - Twitter anti-bot is brutal

### Objective
Port IAC-024 enterprise Twitter scraping code and wrap in BaseScraper interface.

### Deliverables
```
backend/scrapers/
├── base.py                    # BaseScraper abstract class
├── adapters/
│   ├── twitter.py            # Main scraper (from persistent_x_session.py)
│   └── twitter_oauth.py      # OAuth fallback (from playwright_oauth_client.py)
└── data/
    └── twitter_profile/      # Browser profile persistence
```

### Tasks
1. **Copy IAC-024 files (DON'T MODIFY LOGIC)**
   ```bash
   cp /Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py \
      backend/scrapers/adapters/twitter_core.py

   cp /Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/playwright_oauth_client.py \
      backend/scrapers/adapters/twitter_oauth.py
   ```

2. **Create BaseScraper wrapper**
   ```python
   # backend/scrapers/base.py
   from abc import ABC, abstractmethod

   class BaseScraper(ABC):
       @abstractmethod
       def extract(self, target: str) -> dict:
           """Extract raw data from platform"""
           pass

       @abstractmethod
       def normalize(self, raw_data: dict) -> UnifiedContent:
           """Normalize to unified schema"""
           pass
   ```

3. **Wrap existing code**
   ```python
   # backend/scrapers/adapters/twitter.py
   from .twitter_core import PersistentXSession
   from ..base import BaseScraper

   class TwitterScraper(BaseScraper):
       def __init__(self, config):
           self.session = PersistentXSession(
               profile_dir=config.get('profile_dir', 'data/twitter_profile')
           )

       def extract(self, target: str) -> dict:
           return self.session.get_user_tweets(target, limit=100)

       def normalize(self, raw_data: dict) -> UnifiedContent:
           return UnifiedContent(
               platform="twitter",
               source_url=f"https://twitter.com/{raw_data['username']}/status/{raw_data['id']}",
               external_id=raw_data['id'],
               author_id=raw_data['user_id'],
               author_name=raw_data['username'],
               content_type='tweet',
               body=raw_data['text'],
               metrics={'likes': raw_data['likes'], ...}
           )
   ```

4. **Test with @dankoe**
   ```python
   scraper = TwitterScraper({'profile_dir': 'data/twitter_profile'})
   tweets = scraper.extract('dankoe')
   assert len(tweets) >= 10
   ```

5. **Store in database**
   ```python
   for tweet in tweets:
       normalized = scraper.normalize(tweet)
       db.insert_content(normalized)
   ```

### Success Criteria
- [ ] Scrape 10 tweets from @dankoe without ban
- [ ] All anti-detection code working (fingerprint spoofing, human behavior)
- [ ] Session persists across restarts
- [ ] Normalized data stored in PostgreSQL

### Reference Docs
- `docs/pm/IAC024_PORTING_STRATEGY.md` (450 lines - file-by-file guide)
- `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/` (source code)

### Commit Message Template
```
feat(scrapers): Port IAC-024 Twitter scraper with anti-detection

- Copy persistent_x_session.py (1,231 lines enterprise code)
- Copy playwright_oauth_client.py (534 lines OAuth fallback)
- Wrap in BaseScraper interface
- Test scraping @dankoe (10 tweets, no bans)
- Store normalized data in PostgreSQL

Anti-detection: fingerprint spoofing, human behavior, session health
Fallback: Primary (username/password) → OAuth (Google)

Ref: docs/pm/IAC024_PORTING_STRATEGY.md, Package 2
```

---

## 🟩 TEAM 3: Backend API Engineer (Package 3)

**Duration**: 2-3 hours
**Depends on**: Team 1 (database)
**Risk**: LOW - FastAPI is straightforward

### Objective
Create FastAPI backend with universal scraping endpoints.

### Deliverables
```
backend/
├── main.py                # FastAPI app entry point
├── api/
│   ├── routes/
│   │   ├── scrape.py     # POST /scrape endpoint
│   │   ├── query.py      # POST /query/rag endpoint
│   │   └── generate.py   # POST /generate/course-script
│   └── middleware/
│       ├── cors.py       # CORS configuration
│       └── errors.py     # Error handling
└── services/
    ├── scraper_factory.py  # Platform routing
    └── queue.py           # Redis + RQ job queue
```

### Tasks
1. **Create FastAPI scaffold**
   ```python
   # backend/main.py
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware

   app = FastAPI(title="Unified Scraper API")

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Implement /scrape endpoint**
   ```python
   # backend/api/routes/scrape.py
   @router.post("/scrape")
   async def scrape(request: ScrapeRequest):
       """Universal scraping endpoint"""
       scraper = get_scraper(request.platform)  # Factory
       raw_data = await scraper.extract(request.target)
       normalized = scraper.normalize(raw_data)

       # Queue embedding generation
       job = queue.enqueue(generate_embedding, normalized.content_id)

       return {"content_id": str(normalized.content_id), "job_id": job.id}
   ```

3. **Implement scraper factory**
   ```python
   # backend/services/scraper_factory.py
   def get_scraper(platform: str) -> BaseScraper:
       scrapers = {
           "twitter": TwitterScraper,
           "youtube": YouTubeScraper,
           "reddit": RedditScraper,
       }
       return scrapers[platform](config={})
   ```

4. **Add Redis + RQ queue**
   ```python
   # backend/services/queue.py
   from rq import Queue
   from redis import Redis

   redis_conn = Redis()
   queue = Queue(connection=redis_conn)
   ```

5. **Test with cURL**
   ```bash
   curl -X POST http://localhost:8000/scrape \
     -H "Content-Type: application/json" \
     -d '{"platform": "twitter", "target": "dankoe", "limit": 10}'
   ```

### Success Criteria
- [ ] FastAPI runs on http://localhost:8000
- [ ] POST /scrape works for Twitter
- [ ] Swagger docs at http://localhost:8000/docs
- [ ] CORS configured for frontend

### Reference Docs
- `docs/pm/API_SPECIFICATIONS.md` (700 lines - complete endpoint specs)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 3 section)

### Commit Message Template
```
feat(api): Create FastAPI backend with universal scraping

- FastAPI app with CORS middleware
- POST /scrape endpoint (platform factory pattern)
- Redis + RQ queue for async jobs
- Scraper factory (Twitter, YouTube, Reddit)
- Swagger docs at /docs

Endpoints: /scrape, /query/rag, /generate/course-script
Queue: Redis + RQ for rate limit handling

Ref: docs/pm/API_SPECIFICATIONS.md, Package 3
```

---

## 🟨 TEAM 4: YouTube Scraper Specialist (Package 4)

**Duration**: 2-3 hours
**Depends on**: Team 1 (database)
**Risk**: MEDIUM - Transcript availability varies

### Objective
Extract YouTube transcripts with Whisper fallback.

### Deliverables
```
backend/scrapers/adapters/
├── youtube.py            # Main scraper
└── youtube_whisper.py    # Whisper fallback
```

### Pattern to Extract from yt-agent-app
```python
# /Users/kjd/yt-agent-app/youtube-ai-analyzer-prd.md has THIS:

class YouTubeAIAnalyzer:
    def download_audio(self, youtube_url, speed=2.0):
        # yt-dlp audio extraction
        # Speed manipulation with pydub
        pass

    def transcribe_audio(self, audio_path):
        # Whisper transcription
        pass

    def extract_key_insights(self, transcript, video_info):
        # Claude/GPT-4 analysis
        pass
```

### Tasks
1. **Primary: youtube-transcript-api**
   ```python
   from youtube_transcript_api import YouTubeTranscriptApi

   def get_transcript(video_id):
       try:
           return YouTubeTranscriptApi.get_transcript(video_id)
       except TranscriptsDisabled:
           return whisper_fallback(video_id)
   ```

2. **Fallback: Whisper (from yt-agent-app)**
   ```python
   import yt_dlp
   import whisper

   def whisper_fallback(video_id):
       # Download audio
       ydl_opts = {'format': 'bestaudio/best'}
       with yt_dlp.YoutubeDL(ydl_opts) as ydl:
           ydl.download([f"https://youtube.com/watch?v={video_id}"])

       # Transcribe
       model = whisper.load_model("base")
       result = model.transcribe("audio.wav")
       return result["text"]
   ```

3. **Normalize to UnifiedContent**
   ```python
   def normalize(self, raw_data: dict) -> UnifiedContent:
       return UnifiedContent(
           platform="youtube",
           source_url=f"https://youtube.com/watch?v={raw_data['video_id']}",
           external_id=raw_data['video_id'],
           author_name=raw_data['channel_name'],
           content_type='video',
           title=raw_data['title'],
           body=raw_data['transcript'],
           published_at=raw_data['upload_date'],
           metrics={
               'views': raw_data['view_count'],
               'likes': raw_data['like_count'],
           }
       )
   ```

4. **Test with real video**
   ```python
   scraper = YouTubeScraper({})
   video_data = scraper.extract("dQw4w9WgXcQ")  # Rick Astley
   assert len(video_data['transcript']) > 100
   ```

### Success Criteria
- [ ] Extract transcript from video with captions
- [ ] Fallback to Whisper for video without captions
- [ ] Normalized data stored in PostgreSQL
- [ ] Metadata extracted (title, channel, views)

### Reference Docs
- `/Users/kjd/yt-agent-app/youtube-ai-analyzer-prd.md` (627 lines - complete implementation)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 4 section)

### Commit Message Template
```
feat(scrapers): Add YouTube scraper with Whisper fallback

- Primary: youtube-transcript-api (instant)
- Fallback: yt-dlp + Whisper (2 min/video)
- Extract metadata: title, channel, views, likes
- Normalize to UnifiedContent schema
- Test with videos (with/without transcripts)

Pattern extracted from: yt-agent-app
Dependencies: youtube-transcript-api, yt-dlp, openai-whisper

Ref: docs/pm/DAY2_WORK_PACKAGES.md, Package 4
```

---

## 🟪 TEAM 5: Reddit Scraper Specialist (Package 5)

**Duration**: 1-2 hours
**Depends on**: Team 1 (database)
**Risk**: LOW - PRAW is well-documented

### Objective
Scrape Reddit posts and comments using PRAW (official API).

### Deliverables
```
backend/scrapers/adapters/
└── reddit.py              # PRAW scraper
```

### GitHub Patterns Found
From research:
- **JosephLai241/URS**: Universal Reddit Scraper (comprehensive CLI)
- **Rate limit**: 1,000 requests / 10 minutes (OAuth)
- **Best practice**: Rotate User-Agent, respect rate limits

### Tasks
1. **Setup PRAW OAuth**
   ```python
   import praw

   reddit = praw.Reddit(
       client_id=os.getenv("REDDIT_CLIENT_ID"),
       client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
       user_agent="Unified Scraper 1.0 by /u/youruser"
   )
   ```

2. **Scrape subreddit posts**
   ```python
   def extract(self, target: str) -> list:
       subreddit = reddit.subreddit(target)  # "productivity"
       posts = []

       for post in subreddit.hot(limit=50):
           posts.append({
               'id': post.id,
               'title': post.title,
               'body': post.selftext,
               'author': post.author.name,
               'upvotes': post.score,
               'comments': post.num_comments,
               'created_utc': post.created_utc,
           })

       return posts
   ```

3. **Normalize to UnifiedContent**
   ```python
   def normalize(self, raw_data: dict) -> UnifiedContent:
       return UnifiedContent(
           platform="reddit",
           source_url=f"https://reddit.com/r/{raw_data['subreddit']}/comments/{raw_data['id']}",
           external_id=raw_data['id'],
           author_name=raw_data['author'],
           content_type='post',
           title=raw_data['title'],
           body=raw_data['body'],
           metrics={
               'upvotes': raw_data['upvotes'],
               'comments': raw_data['comments'],
           }
       )
   ```

4. **Test with r/productivity**
   ```python
   scraper = RedditScraper({})
   posts = scraper.extract('productivity')
   assert len(posts) == 50
   ```

### Success Criteria
- [ ] Scrape 50 posts from r/productivity
- [ ] Rate limit respected (1,000/10min)
- [ ] Normalized data stored in PostgreSQL
- [ ] Comments optional (defer to Week 2)

### Reference Docs
- GitHub: JosephLai241/URS (Universal Reddit Scraper patterns)
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 5 section)

### Commit Message Template
```
feat(scrapers): Add Reddit scraper using PRAW

- PRAW OAuth setup (client_id, client_secret)
- Scrape subreddit posts (hot, limit=50)
- Respect rate limits (1,000 req/10min)
- Normalize to UnifiedContent schema
- Test with r/productivity (50 posts)

Dependencies: praw
Rate limit: 1,000/10min OAuth, 100/10min no auth

Ref: docs/pm/DAY2_WORK_PACKAGES.md, Package 5
```

---

## 🟧 TEAM 6: RAG/ChromaDB Engineer (Package 6)

**Duration**: 2-3 hours
**Depends on**: Team 1 (database)
**Risk**: MEDIUM - Embedding generation can be slow

### Objective
Set up ChromaDB for semantic search with OpenAI embeddings.

### Deliverables
```
backend/services/
├── embeddings.py         # OpenAI embedding generation
├── chromadb_client.py    # ChromaDB setup
└── rag_query.py          # Semantic search
```

### Tasks
1. **Setup ChromaDB with persistence**
   ```python
   import chromadb
   from chromadb.config import Settings

   client = chromadb.Client(Settings(
       chroma_db_impl="duckdb+parquet",
       persist_directory="./data/chromadb"  # NOT /tmp
   ))

   collection = client.create_collection(
       name="unified_content",
       metadata={"hnsw:space": "cosine"}
   )
   ```

2. **Generate OpenAI embeddings**
   ```python
   from openai import OpenAI

   openai_client = OpenAI()

   def generate_embedding(text: str) -> list[float]:
       response = openai_client.embeddings.create(
           model="text-embedding-3-small",  # 1536 dims, $0.00002/1K tokens
           input=text
       )
       return response.data[0].embedding
   ```

3. **Batch insert (100 at a time)**
   ```python
   def index_content(contents: list[UnifiedContent]):
       embeddings = [generate_embedding(c.body) for c in contents]

       collection.add(
           documents=[c.body for c in contents],
           embeddings=embeddings,
           metadatas=[c.dict() for c in contents],
           ids=[str(c.content_id) for c in contents]
       )
   ```

4. **Semantic search**
   ```python
   def search(query: str, limit=20):
       query_embedding = generate_embedding(query)

       results = collection.query(
           query_embeddings=[query_embedding],
           n_results=limit,
           where={"platform": "twitter"}  # Optional filter
       )

       return results
   ```

5. **Test query**
   ```python
   results = search("What does Dan Koe say about focus?", limit=10)
   assert len(results['documents']) == 10
   ```

### Success Criteria
- [ ] ChromaDB persists to `./data/chromadb`
- [ ] Generate embeddings for 100 items
- [ ] Semantic search returns in <2 seconds
- [ ] Similarity threshold >0.7 for relevant results

### Reference Docs
- `docs/pm/DAY2_WORK_PACKAGES.md` (Package 6 section)
- `docs/pm/DATABASE_SCHEMA.md` (embedding strategy)

### Commit Message Template
```
feat(rag): Setup ChromaDB with OpenAI embeddings

- ChromaDB with persistence (./data/chromadb)
- OpenAI text-embedding-3-small (1536 dims)
- Batch embedding generation (100/request)
- Semantic search with cosine similarity
- Test query: "Dan Koe focus" (10 results)

Cost: $0.00002/1K tokens = $0.20 per 10K items
Speed: 100 embeddings = ~5 seconds

Ref: docs/pm/DAY2_WORK_PACKAGES.md, Package 6
```

---

## Execution Order

### Phase 1: Foundation (SEQUENTIAL)
```
🔴 TEAM 1 → Database Setup (1-2h)
    ⬇️ BLOCKS EVERYONE
    ✅ Database ready
```

### Phase 2: Parallel Execution (SIMULTANEOUS)
```
🟦 TEAM 2 → Twitter Scraper   (3-4h)  ┐
🟩 TEAM 3 → Backend API       (2-3h)  ├─ All start at same time
🟨 TEAM 4 → YouTube Scraper   (2-3h)  │  after Team 1 completes
🟪 TEAM 5 → Reddit Scraper    (1-2h)  │
🟧 TEAM 6 → RAG/ChromaDB      (2-3h)  ┘

Total time: MAX(3-4h) = ~4 hours
```

### Phase 3: Integration (Team 3 waits for 2, 4, 5, 6)
```
🟩 TEAM 3 integrates all scrapers into API
    ⬇️
    ✅ Full MVP ready
```

**Total Day 2 Time**: 1-2h + 4h + 1h integration = **6-7 hours**

---

## CCW Spawn Commands

### Spawn Team 1 (FIRST)
```bash
# Create GitHub issue
gh issue create \
  --title "Package 1: Database Setup (PostgreSQL + pgvector)" \
  --body "See docs/pm/DAY2_WORK_PACKAGES.md Package 1" \
  --label "critical"

# In CCW: Paste Package 1 prompt from DAY2_WORK_PACKAGES.md
```

### After Team 1 completes: Spawn Teams 2-6 (PARALLEL)
```bash
# Spawn 5 CCW agents simultaneously
# Each agent gets their package prompt from DAY2_WORK_PACKAGES.md

Agent 1 → Package 2 (Twitter)
Agent 2 → Package 3 (FastAPI)
Agent 3 → Package 4 (YouTube)
Agent 4 → Package 5 (Reddit)
Agent 5 → Package 6 (ChromaDB)
```

---

## Risk Mitigation

| Team | Risk | Mitigation |
|------|------|------------|
| Team 1 | PostgreSQL setup fails | Fallback: SQLite + sqlite-vss |
| Team 2 | Twitter bans | Use IAC-024 code 100% as-is |
| Team 3 | API complexity | Start simple (1 endpoint), iterate |
| Team 4 | No transcripts | Whisper fallback tested in yt-agent-app |
| Team 5 | OAuth setup friction | Provide shared credentials |
| Team 6 | Embedding costs | Batch 100/request, use cheaper model |

---

## What We Have Already

### Scrapers to Nick Patterns From:
1. ✅ **Twitter**: IAC-024 (1,765 lines proven)
2. ✅ **YouTube**: yt-agent-app (627 lines with Whisper)
3. ✅ **Reddit**: GitHub URS patterns
4. ❌ **Amazon**: Need to find (ScraperAPI has structured endpoint)
5. ❌ **Web**: Basic (BeautifulSoup + ScraperAPI)

### Infrastructure Ready:
- ✅ Database schema designed (600 lines)
- ✅ API specs documented (700 lines)
- ✅ Porting strategy detailed (450 lines)
- ✅ Work packages written (850 lines)

**We're not starting from scratch - we're assembling proven patterns.**

---

## Next: User Validation

Before spawning teams, answer:
1. **Which scrapers are priority?** (Twitter, YouTube, Reddit confirmed)
2. **Do we need Amazon for MVP?** (Or defer to Week 2?)
3. **Should Team 3 build full API or just /scrape?** (Start minimal?)
4. **Tauri frontend Week 2 confirmed?** (Yes, backend-only MVP)

Let me know and I'll spawn the teams immediately.
