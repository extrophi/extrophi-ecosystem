# IAC-024 Code Porting Strategy

**Source**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/`
**Target**: `/Users/kjd/01-projects/IAC-032-unified-scraper/backend/`
**Goal**: Reuse 100% proven Twitter scraping code, extend for multi-platform

---

## Files to Port (Priority Order)

### CRITICAL (Port First - Day 2 Morning)

#### 1. `src/scrapers/persistent_x_session.py` → `backend/scrapers/adapters/twitter.py`

**Size**: 1,231 lines
**Why Critical**: Enterprise-grade Twitter scraping with anti-detection
**Estimated Port Time**: 2-3 hours

**What It Contains**:
```python
class AdvancedFingerprintSpoofing:
    - get_realistic_viewport()
    - get_realistic_user_agent()
    - apply_stealth_scripts(page)  # 200+ lines of anti-bot JavaScript

class HumanBehaviorSimulator:
    - human_mouse_move(page, x, y)  # Curved paths with Bezier curves
    - human_type(page, selector, text)  # Typing speed 50-120 ms/char
    - human_scroll(page, direction, amount)
    - random_activity(page)  # Mimics real browsing

class SessionHealthMonitor:
    - record_activity()
    - is_healthy() -> bool
    - needs_maintenance() -> bool
    - get_health_report() -> Dict

class IntelligentRateLimit:
    - record_request(success: bool)
    - get_current_load() -> Dict
    - apply_rate_limit()  # Adaptive delays with jitter
    - should_back_off() -> bool

class PersistentXSession:
    - initialize_session()  # Browser + profile setup
    - authenticate()  # Username/password login
    - get_user_tweets(username, limit)
    - search_tweets(query, limit)
    - maintain_session_health()
    - _extract_tweet_data(tweet_element)  # Parses Twitter DOM
```

**Porting Changes**:
```python
# BEFORE (IAC-024)
class PersistentXSession:
    def __init__(self, profile_dir="data/browser_profile"):
        self.profile_dir = profile_dir
        # ...

# AFTER (IAC-032 - Unified)
from .base import BaseScraper, UnifiedContent

class TwitterScraper(BaseScraper):
    def __init__(self, config: dict):
        super().__init__(config)
        self.session = PersistentXSession(
            profile_dir=config.get('profile_dir', 'data/browser_profile')
        )

    def extract(self, url: str) -> dict:
        """Extract raw tweet data"""
        tweet_data = self.session.get_user_tweets(username, limit=1)
        return tweet_data[0] if tweet_data else None

    def normalize(self, raw_data: dict) -> UnifiedContent:
        """Convert to unified schema"""
        return UnifiedContent(
            platform="twitter",
            source_url=f"https://twitter.com/{raw_data['username']}/status/{raw_data['id']}",
            external_id=raw_data['id'],
            author_id=raw_data['user_id'],
            author_name=raw_data['username'],
            content_type='tweet',
            body=raw_data['text'],
            published_at=raw_data['created_at'],
            metrics={
                'likes': raw_data['likes'],
                'retweets': raw_data['retweets'],
                'replies': raw_data['replies'],
                'views': raw_data.get('views', 0),
                'engagement_rate': self._calculate_engagement(raw_data)
            }
        )
```

**Testing After Port**:
```bash
# Test basic scraping
python -c "
from backend.scrapers.adapters.twitter import TwitterScraper
scraper = TwitterScraper({'profile_dir': 'data/twitter_profile'})
tweets = scraper.get_user_tweets('dankoe', limit=10)
print(f'Scraped {len(tweets)} tweets')
"
```

---

#### 2. `src/scrapers/playwright_oauth_client.py` → `backend/scrapers/adapters/twitter_oauth.py`

**Size**: 534 lines
**Why Critical**: Google OAuth for @iamcodio account
**Estimated Port Time**: 1-2 hours

**What It Contains**:
```python
class PlaywrightOAuthClient:
    - setup_browser(headless=False)  # Chrome with profile
    - login_with_google()  # OAuth flow
    - check_login() -> bool
    - search_tweets(query, limit)
    - get_user_tweets(username, limit)
    - _apply_rate_limit()  # 100 req/hour, 3s minimum interval
    - _save_session()  # Persist cookies to data/twitter_session.json
```

**Porting Strategy**:
- Keep as fallback OAuth method
- Primary: `persistent_x_session.py` (username/password)
- Secondary: `playwright_oauth_client.py` (Google OAuth for @iamcodio)
- Use case: If primary session expires, fall back to OAuth

**Integration**:
```python
class TwitterScraper(BaseScraper):
    def __init__(self, config):
        self.primary = PersistentXSession(...)
        self.fallback = PlaywrightOAuthClient(...)

    def extract(self, url):
        try:
            return self.primary.get_user_tweets(...)
        except AuthenticationError:
            logger.warning("Primary session failed, falling back to OAuth")
            return self.fallback.get_user_tweets(...)
```

---

### IMPORTANT (Port Second - Day 2 Afternoon)

#### 3. `src/models/tweet_models.py` → `backend/models/content_models.py`

**Size**: ~150 lines
**Why Important**: Proven Pydantic models
**Estimated Port Time**: 30 minutes

**Existing Models**:
```python
class Tweet(BaseModel):
    id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    likes: int
    retweets: int
    replies: int
    views: Optional[int]
    is_thread: bool
    media_urls: List[str]
    hashtags: List[str]

class User(BaseModel):
    id: str
    username: str
    display_name: str
    bio: Optional[str]
    followers_count: int
    verified: bool
```

**Extend to Unified**:
```python
class UnifiedContent(BaseModel):
    content_id: UUID = Field(default_factory=uuid4)
    platform: Literal["twitter", "youtube", "reddit", "amazon", "web"]
    source_url: str
    external_id: Optional[str]

    # Author (generic across platforms)
    author_id: str
    author_name: str
    author_handle: Optional[str]

    # Content
    content_type: str  # 'tweet', 'video', 'post', 'review'
    title: Optional[str]
    body: str
    language: str = "en"

    # Metrics (JSONB-compatible dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    published_at: Optional[datetime]
    scraped_at: datetime = Field(default_factory=datetime.now)

    # Analysis (populated by LLM)
    analysis: Dict[str, Any] = Field(default_factory=dict)

    # Vector embedding
    embedding: Optional[List[float]] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
```

---

#### 4. `src/database/schema.py` → `backend/db/connection.py`

**Size**: ~200 lines
**Why Important**: Database CRUD patterns
**Estimated Port Time**: 1 hour

**Existing Patterns** (SQLite):
```python
class Database:
    def __init__(self, db_path="data/tweets.db"):
        self.conn = sqlite3.connect(db_path)

    def insert_tweet(self, tweet_data):
        # INSERT with conflict handling
        pass

    def get_tweets(self, limit=100):
        # SELECT with pagination
        pass

    def search_tweets(self, query):
        # Full-text search
        pass
```

**Port to PostgreSQL**:
```python
from sqlalchemy import create_engine, Column, String, Integer, JSONB
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector

class Database:
    def __init__(self, db_url="postgresql://localhost/unified_scraper"):
        self.engine = create_engine(db_url)

    def insert_content(self, content: UnifiedContent):
        with self.engine.begin() as conn:
            conn.execute(
                contents_table.insert().values(
                    id=content.content_id,
                    platform=content.platform,
                    body=content.body,
                    metrics=content.metrics,  # JSONB
                    embedding=content.embedding  # vector(1536)
                )
            )

    def search_by_embedding(self, query_embedding, limit=10):
        # Vector similarity search using <=> operator
        with self.engine.connect() as conn:
            result = conn.execute(
                f"""
                SELECT *, 1 - (embedding <=> :query) as similarity
                FROM contents
                ORDER BY embedding <=> :query
                LIMIT :limit
                """,
                {"query": query_embedding, "limit": limit}
            )
            return result.fetchall()
```

---

### USEFUL (Port Third - Day 3 or Week 2)

#### 5. `src/analysis/viral_predictor.py` → `backend/services/viral_predictor.py`

**Size**: ~100 lines
**Estimated Port Time**: 30 minutes

**Simple ML model predicting tweet virality**:
```python
def predict_viral_score(tweet: Tweet) -> float:
    # Features: length, media, time, hashtags, historical performance
    features = [
        len(tweet.content),
        1 if tweet.media_urls else 0,
        tweet.created_at.hour,  # Best posting times
        len(tweet.hashtags),
        # User's historical avg engagement
    ]
    # Simple logistic regression or use GPT-4 for prediction
    return score  # 0-100
```

**Port Strategy**: Copy as-is, works with UnifiedContent.

---

#### 6. `src/api/main_playwright.py` → `backend/api/main.py`

**Size**: ~150 lines
**Estimated Port Time**: 1 hour

**FastAPI structure**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Tweet Hunter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    global twitter_session
    twitter_session = PersistentXSession()
    await twitter_session.initialize_session()

@app.get("/scrape/user/{username}")
async def scrape_user(username: str, limit: int = 20):
    tweets = await twitter_session.get_user_tweets(username, limit)
    return {"tweets": [t.dict() for t in tweets]}
```

**Extend for Multi-Platform**:
```python
@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    """Universal scraping endpoint"""
    scraper = get_scraper(request.platform)  # Factory pattern
    raw_data = scraper.extract(request.url)
    normalized = scraper.normalize(raw_data)

    # Store in database
    db.insert_content(normalized)

    # Generate embedding
    embedding = await generate_embedding(normalized.body)
    db.update_embedding(normalized.content_id, embedding)

    return {"content_id": str(normalized.content_id)}
```

---

## Porting Checklist

### Day 2 Morning (4 hours)
- [ ] Port `persistent_x_session.py` → `twitter.py`
- [ ] Wrap in `BaseScraper` interface
- [ ] Test with @dankoe (scrape 10 tweets)
- [ ] Verify fingerprint spoofing still works
- [ ] Test session persistence (restart + reuse)

### Day 2 Afternoon (4 hours)
- [ ] Port `playwright_oauth_client.py` → `twitter_oauth.py`
- [ ] Port `tweet_models.py` → `content_models.py`
- [ ] Extend to `UnifiedContent` schema
- [ ] Port `schema.py` database patterns
- [ ] Migrate to PostgreSQL with pgvector
- [ ] Test full pipeline: scrape → normalize → store → search

### Day 3 or Week 2
- [ ] Port `viral_predictor.py`
- [ ] Port `main_playwright.py` API structure
- [ ] Add multi-platform routing
- [ ] Port any useful utility functions

---

## Testing Strategy

### Unit Tests
```python
# tests/test_twitter_scraper.py
def test_normalize_tweet():
    raw = {
        'id': '123',
        'username': 'dankoe',
        'text': 'Focus test',
        'likes': 100
    }
    scraper = TwitterScraper({})
    normalized = scraper.normalize(raw)

    assert normalized.platform == 'twitter'
    assert normalized.body == 'Focus test'
    assert normalized.metrics['likes'] == 100
```

### Integration Tests
```python
# tests/test_twitter_integration.py
@pytest.mark.slow
async def test_scrape_dankoe():
    scraper = TwitterScraper({'profile_dir': 'data/test_profile'})
    tweets = await scraper.get_user_tweets('dankoe', limit=5)

    assert len(tweets) == 5
    assert all(t.platform == 'twitter' for t in tweets)
    assert all(t.author_handle == '@dankoe' for t in tweets)
```

---

## Risk Mitigation

### Risk 1: Twitter Detects Bot Activity
**Mitigation**: All anti-detection code from `persistent_x_session.py` ports directly. Already proven with @iamcodio account.

### Risk 2: Session Expires During Port
**Mitigation**: Keep IAC-024 running in parallel. Can fall back to old code if new implementation fails.

### Risk 3: Database Migration Breaks Existing Data
**Mitigation**: Export IAC-024 SQLite to CSV first. Test migration on sample data before full import.

### Risk 4: Performance Regression
**Mitigation**: Benchmark before/after. Target: <5s per tweet (IAC-024 current performance).

---

## Data Migration Plan

```bash
# Export from IAC-024 (SQLite)
cd /Users/kjd/01-projects/IAC-024-tweet-hunter
sqlite3 data/tweets.db ".mode csv" ".headers on" ".output tweets_export.csv" "SELECT * FROM tweets;"

# Import to IAC-032 (PostgreSQL)
cd /Users/kjd/01-projects/IAC-032-unified-scraper
psql unified_scraper -c "COPY contents(
    platform, source_url, external_id, author_id, author_name,
    content_type, body, published_at, metrics
) FROM 'tweets_export.csv' CSV HEADER;"
```

---

## File Mapping Summary

| IAC-024 Source | IAC-032 Target | Priority | Time |
|----------------|----------------|----------|------|
| `src/scrapers/persistent_x_session.py` | `backend/scrapers/adapters/twitter.py` | CRITICAL | 2-3h |
| `src/scrapers/playwright_oauth_client.py` | `backend/scrapers/adapters/twitter_oauth.py` | CRITICAL | 1-2h |
| `src/models/tweet_models.py` | `backend/models/content_models.py` | HIGH | 30min |
| `src/database/schema.py` | `backend/db/connection.py` | HIGH | 1h |
| `src/analysis/viral_predictor.py` | `backend/services/viral_predictor.py` | MEDIUM | 30min |
| `src/api/main_playwright.py` | `backend/api/main.py` | MEDIUM | 1h |

**Total Porting Time: 6-8 hours (Day 2)**

---

**This porting strategy ensures we reuse 100% proven code while extending for multi-platform capability.**
