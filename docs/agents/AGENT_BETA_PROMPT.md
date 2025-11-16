# AGENT BETA: Twitter Scraper Implementation

## MISSION CRITICAL: Port Enterprise Anti-Detection Code

**Agent ID**: Beta
**Role**: Twitter Platform Adapter
**Priority**: HIGHEST (85% fail rate without proper anti-detection)
**Estimated Time**: 2-3 hours

---

## EXECUTIVE SUMMARY

Port proven enterprise-grade Twitter scraping code from IAC-024 Tweet Hunter project. This code has been battle-tested against Twitter's aggressive bot detection system and successfully operates with @iamcodio account. Your job is to wrap this existing code in the new BaseScraper interface for the unified multi-platform architecture.

**CRITICAL**: Do NOT write new Twitter scraping code. REUSE the 1,765 lines of proven anti-detection code from IAC-024. Twitter bans 85% of naive scrapers within minutes.

---

## SOURCE CODE LOCATIONS

### 1. Primary Scraper (1,231 lines) - COPY THIS
**Path**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py`

Contains:
- `AdvancedFingerprintSpoofing` class (Canvas, WebGL, Audio, Battery, Performance timing)
- `HumanBehaviorSimulator` class (Curved mouse movements, typing variation, natural scrolling)
- `SessionHealthMonitor` class (Activity tracking, session age monitoring, health degradation detection)
- `IntelligentRateLimit` class (Adaptive backoff, burst detection, success streak tracking)
- `PersistentXSession` class (Session persistence, authentication, tweet extraction)

### 2. OAuth Handler (534 lines) - COPY THIS
**Path**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/playwright_oauth_client.py`

Contains:
- `PlaywrightOAuthClient` class
- Google OAuth flow handling
- Chrome profile persistence
- Session cookie management
- Rate limiting (hourly limits, minimum intervals)

### 3. Data Models (154 lines) - REFERENCE
**Path**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/models/tweet_models.py`

Reference for Tweet/User Pydantic models (will be adapted to UnifiedContent schema).

---

## FILES TO CREATE

### Directory Structure
```
backend/
  scrapers/
    __init__.py                           # Package exports
    base.py                               # BaseScraper ABC (CRITICAL INTERFACE)
    adapters/
      __init__.py                         # Adapter exports
      twitter.py                          # TwitterScraper (wrapper implementing BaseScraper)
      _persistent_x_session.py            # COPY from IAC-024 (anti-detection engine)
      _playwright_oauth.py                # COPY from IAC-024 (OAuth handler)
```

---

## STEP 1: Create Package Structure

### File: `backend/scrapers/__init__.py`
```python
"""
Unified Scraper - Platform Scrapers
Multi-platform content intelligence engine
"""

from .base import BaseScraper
from .adapters.twitter import TwitterScraper

__all__ = ["BaseScraper", "TwitterScraper"]
```

### File: `backend/scrapers/adapters/__init__.py`
```python
"""
Platform-specific scraper adapters
Each adapter implements the BaseScraper interface
"""

from .twitter import TwitterScraper

__all__ = ["TwitterScraper"]
```

---

## STEP 2: Create BaseScraper Abstract Base Class

### File: `backend/scrapers/base.py`

```python
"""
Base Scraper Interface - Abstract Base Class
All platform adapters must implement this interface
"""

from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AuthorModel(BaseModel):
    """Author information"""
    id: str
    username: str
    display_name: str
    followers_count: int = 0
    verified: bool = False
    profile_url: str


class ContentModel(BaseModel):
    """Content body and metadata"""
    title: str = ""
    body: str
    word_count: int
    char_count: int
    language: str = "en"


class MetricsModel(BaseModel):
    """Engagement metrics"""
    likes: int = 0
    shares: int = 0  # retweets, reposts, etc.
    comments: int = 0  # replies, comments, etc.
    views: int = 0
    engagement_rate: float = 0.0


class AnalysisModel(BaseModel):
    """LLM analysis results (populated later)"""
    frameworks: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    quality_score: float = 0.0


class UnifiedContent(BaseModel):
    """
    Unified content schema across all platforms
    Maps to PostgreSQL 'contents' table
    """
    content_id: UUID = Field(default_factory=uuid4)
    platform: str  # 'twitter', 'youtube', 'reddit', 'amazon', 'web'
    source_url: str
    author: AuthorModel
    content: ContentModel
    metrics: MetricsModel
    analysis: AnalysisModel = Field(default_factory=AnalysisModel)
    embedding: list[float] = Field(default_factory=list)  # 1536 dims for OpenAI
    published_at: datetime
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BaseScraper(ABC):
    """
    Abstract Base Class for all platform scrapers

    All platform adapters (Twitter, YouTube, Reddit, etc.) must implement:
    1. health_check() - Verify scraper is operational
    2. extract() - Fetch raw data from platform
    3. normalize() - Convert raw data to UnifiedContent

    This ensures consistent interface across all platforms.
    """

    @abstractmethod
    async def health_check(self) -> dict:
        """
        Check if scraper is operational

        Returns:
            dict: Health status including:
                - status: 'healthy' | 'degraded' | 'unhealthy'
                - authenticated: bool
                - rate_limit_remaining: int
                - session_age_seconds: float
                - last_activity_seconds: float
                - error_count: int
        """
        pass

    @abstractmethod
    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract raw data from platform

        Args:
            target: Platform-specific target (username, video_id, subreddit, etc.)
            limit: Maximum number of items to extract

        Returns:
            list[dict]: Raw platform data (not yet normalized)
        """
        pass

    @abstractmethod
    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Convert raw platform data to UnifiedContent schema

        Args:
            raw_data: Single raw data item from extract()

        Returns:
            UnifiedContent: Normalized data for PostgreSQL storage
        """
        pass

    async def scrape(self, target: str, limit: int = 20) -> list[UnifiedContent]:
        """
        High-level scrape operation (extract + normalize)

        Args:
            target: Platform-specific target
            limit: Maximum items to scrape

        Returns:
            list[UnifiedContent]: Normalized content ready for storage
        """
        raw_items = await self.extract(target, limit)
        normalized = []
        for item in raw_items:
            try:
                content = await self.normalize(item)
                normalized.append(content)
            except Exception as e:
                print(f"Failed to normalize item: {e}")
                continue
        return normalized
```

---

## STEP 3: Copy Anti-Detection Engine

### File: `backend/scrapers/adapters/_persistent_x_session.py`

**INSTRUCTIONS**:
1. Copy ENTIRE content from `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/persistent_x_session.py`
2. Modify imports at the top:

**Change FROM**:
```python
from ..models.tweet_models import Tweet, User
from ..database.schema import Database
```

**Change TO**:
```python
# These imports will be handled by TwitterScraper wrapper
# For now, define minimal Tweet class inline for compatibility

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Tweet(BaseModel):
    """Minimal Tweet model for internal use"""
    id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: Optional[int] = None
    media_urls: List[str] = []
    hashtags: List[str] = []
    mentions: List[str] = []
    urls: List[str] = []


class MockDatabase:
    """Mock database for standalone operation"""
    def insert_tweet(self, tweet_dict):
        pass  # Will be replaced by PostgreSQL in TwitterScraper
```

3. Replace `self.db = Database()` with `self.db = MockDatabase()`

4. Keep ALL other code exactly as-is:
   - AdvancedFingerprintSpoofing (lines 27-196)
   - HumanBehaviorSimulator (lines 199-291)
   - SessionHealthMonitor (lines 294-341)
   - IntelligentRateLimit (lines 344-428)
   - PersistentXSession (lines 431-1199)
   - create_persistent_session() (lines 1202-1211)

---

## STEP 4: Copy OAuth Handler

### File: `backend/scrapers/adapters/_playwright_oauth.py`

**INSTRUCTIONS**:
1. Copy ENTIRE content from `/Users/kjd/01-projects/IAC-024-tweet-hunter/src/scrapers/playwright_oauth_client.py`
2. Apply same import modifications as _persistent_x_session.py

**CRITICAL CODE TO PRESERVE** (DO NOT MODIFY):
- Anti-detection browser arguments (lines 85-89, 100-108)
- Webdriver property hiding (lines 137-148)
- Rate limiting logic (lines 151-178)
- Session cookie persistence (lines 113-133)

---

## STEP 5: Create TwitterScraper Wrapper

### File: `backend/scrapers/adapters/twitter.py`

```python
"""
Twitter Scraper Adapter
Implements BaseScraper interface using proven IAC-024 anti-detection code
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from ..base import (
    BaseScraper,
    UnifiedContent,
    AuthorModel,
    ContentModel,
    MetricsModel,
    AnalysisModel
)
from ._persistent_x_session import (
    PersistentXSession,
    create_persistent_session,
    Tweet
)


class TwitterScraper(BaseScraper):
    """
    Twitter platform adapter with enterprise-grade anti-detection

    Features:
    - Canvas/WebGL/Audio fingerprint spoofing
    - Human behavior simulation (curved mouse, typing variation)
    - Session health monitoring and auto-recovery
    - Intelligent adaptive rate limiting
    - Persistent authentication across restarts
    """

    def __init__(self):
        self.session: Optional[PersistentXSession] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize persistent Twitter session

        Returns:
            bool: True if session initialized successfully
        """
        if self._initialized and self.session:
            return True

        try:
            self.session = await create_persistent_session()
            self._initialized = True
            print("TwitterScraper initialized with anti-detection")
            return True
        except Exception as e:
            print(f"Failed to initialize TwitterScraper: {e}")
            return False

    async def health_check(self) -> dict:
        """
        Check Twitter scraper health status

        Returns:
            dict: Health metrics including session status, rate limits, and errors
        """
        if not self.session:
            return {
                "status": "unhealthy",
                "authenticated": False,
                "rate_limit_remaining": 0,
                "session_age_seconds": 0,
                "last_activity_seconds": 0,
                "error_count": 0,
                "message": "Session not initialized"
            }

        is_healthy = self.session.health.is_healthy()
        load = self.session.rate_limit.get_current_load()

        return {
            "status": "healthy" if is_healthy else "degraded",
            "authenticated": self.session.authenticated,
            "rate_limit_remaining": self.session.rate_limit.hourly_limit - load['hourly'],
            "session_age_seconds": self.session.health.get_session_age(),
            "last_activity_seconds": self.session.health.time_since_last_activity(),
            "error_count": self.session.health.error_count,
            "success_rate": load['success_rate'],
            "backoff_multiplier": self.session.rate_limit.backoff_multiplier,
            "message": "Session operational" if is_healthy else "Session needs maintenance"
        }

    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract tweets from a Twitter user

        Args:
            target: Twitter username (without @)
            limit: Maximum number of tweets to extract (default 20)

        Returns:
            list[dict]: Raw tweet data from Twitter
        """
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize Twitter session")

        # Use the proven extraction method
        tweets: list[Tweet] = await self.session.get_user_tweets(target, limit)

        # Convert Pydantic models to dicts
        raw_data = []
        for tweet in tweets:
            raw_data.append({
                "id": tweet.id,
                "user_id": tweet.user_id,
                "username": tweet.username,
                "content": tweet.content,
                "created_at": tweet.created_at,
                "likes": tweet.likes,
                "retweets": tweet.retweets,
                "replies": tweet.replies,
                "views": tweet.views,
                "media_urls": tweet.media_urls,
                "hashtags": tweet.hashtags,
                "mentions": tweet.mentions,
                "urls": tweet.urls
            })

        return raw_data

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Normalize Twitter data to UnifiedContent schema

        Args:
            raw_data: Single tweet dictionary from extract()

        Returns:
            UnifiedContent: Normalized content for PostgreSQL
        """
        username = raw_data.get("username", "unknown")
        content_text = raw_data.get("content", "")

        # Build author model
        author = AuthorModel(
            id=raw_data.get("user_id", username),
            username=username,
            display_name=username,  # Twitter doesn't provide display name in tweet
            followers_count=0,  # Would need separate user lookup
            verified=False,
            profile_url=f"https://x.com/{username}"
        )

        # Build content model
        content = ContentModel(
            title="",  # Tweets don't have titles
            body=content_text,
            word_count=len(content_text.split()),
            char_count=len(content_text),
            language="en"  # Would need detection
        )

        # Build metrics model
        likes = raw_data.get("likes", 0)
        shares = raw_data.get("retweets", 0)
        comments = raw_data.get("replies", 0)
        views = raw_data.get("views", 0) or 0

        # Calculate engagement rate
        total_engagement = likes + shares + comments
        engagement_rate = (total_engagement / max(views, 1)) * 100 if views > 0 else 0.0

        metrics = MetricsModel(
            likes=likes,
            shares=shares,
            comments=comments,
            views=views,
            engagement_rate=round(engagement_rate, 4)
        )

        # Empty analysis (to be filled by LLM later)
        analysis = AnalysisModel()

        # Build unified content
        unified = UnifiedContent(
            content_id=uuid4(),
            platform="twitter",
            source_url=f"https://x.com/{username}/status/{raw_data.get('id', 'unknown')}",
            author=author,
            content=content,
            metrics=metrics,
            analysis=analysis,
            embedding=[],  # To be filled by embedding service
            published_at=raw_data.get("created_at", datetime.utcnow()),
            scraped_at=datetime.utcnow(),
            metadata={
                "tweet_id": raw_data.get("id"),
                "hashtags": raw_data.get("hashtags", []),
                "mentions": raw_data.get("mentions", []),
                "media_urls": raw_data.get("media_urls", []),
                "external_urls": raw_data.get("urls", [])
            }
        )

        return unified

    async def search_tweets(self, query: str, limit: int = 20) -> list[UnifiedContent]:
        """
        Search tweets by query (additional feature beyond BaseScraper)

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            list[UnifiedContent]: Normalized search results
        """
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize Twitter session")

        tweets = await self.session.search_tweets(query, limit)

        results = []
        for tweet in tweets:
            raw = {
                "id": tweet.id,
                "user_id": tweet.user_id,
                "username": tweet.username,
                "content": tweet.content,
                "created_at": tweet.created_at,
                "likes": tweet.likes,
                "retweets": tweet.retweets,
                "replies": tweet.replies,
                "views": tweet.views,
                "media_urls": tweet.media_urls,
                "hashtags": tweet.hashtags,
                "mentions": tweet.mentions,
                "urls": tweet.urls
            }
            normalized = await self.normalize(raw)
            results.append(normalized)

        return results

    async def close(self):
        """Gracefully close Twitter session"""
        if self.session:
            await self.session.close()
            self.session = None
            self._initialized = False
            print("TwitterScraper session closed")

    def __del__(self):
        """Cleanup on deletion"""
        if self.session and self._initialized:
            # Can't await in __del__, just note it needs cleanup
            print("Warning: TwitterScraper not properly closed. Call close() method.")


# Convenience function for quick testing
async def test_twitter_scraper():
    """Test TwitterScraper with @dankoe"""
    scraper = TwitterScraper()

    print("Initializing TwitterScraper...")
    await scraper.initialize()

    print("\nChecking health...")
    health = await scraper.health_check()
    print(f"Health: {health}")

    print("\nScraping 10 tweets from @dankoe...")
    tweets = await scraper.scrape("dankoe", limit=10)

    for i, tweet in enumerate(tweets, 1):
        print(f"\n--- Tweet {i} ---")
        print(f"Platform: {tweet.platform}")
        print(f"Author: @{tweet.author.username}")
        print(f"Content: {tweet.content.body[:100]}...")
        print(f"Metrics: {tweet.metrics.likes} likes, {tweet.metrics.shares} retweets")
        print(f"URL: {tweet.source_url}")

    await scraper.close()

    return tweets


if __name__ == "__main__":
    asyncio.run(test_twitter_scraper())
```

---

## STEP 6: Update Dependencies

### Add to `backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing deps ...

    # Twitter Scraping (Anti-Detection)
    "playwright>=1.40.0",
    "playwright-stealth>=1.0.6",
    "python-dotenv>=1.0.0",

    # Fallback browser automation
    "pyppeteer>=1.0.2",
]

[tool.uv.sources]
# No custom sources needed
```

### Post-install script (run once):
```bash
# Install Playwright browsers
playwright install chromium
playwright install-deps
```

---

## ANTI-DETECTION FEATURES (DO NOT MODIFY)

### 1. Canvas Fingerprint Spoofing
```javascript
// Lines 148-157 in persistent_x_session.py
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(...args) {
    const context = this.getContext('2d');
    if (context) {
        context.fillStyle = 'rgba(' + Math.floor(Math.random() * 256) + ',' +
                            Math.floor(Math.random() * 256) + ',' +
                            Math.floor(Math.random() * 256) + ', 0.01)';
        context.fillRect(0, 0, 1, 1);
    }
    return originalToDataURL.apply(this, args);
};
```
**Purpose**: Adds imperceptible noise to canvas fingerprints, preventing unique identification.

### 2. WebGL Fingerprint Spoofing
```javascript
// Lines 137-146
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter(parameter);
};
```
**Purpose**: Returns common hardware identifiers to blend with majority of users.

### 3. Audio Context Fingerprinting
```javascript
// Lines 159-171
const AudioContext = window.AudioContext || window.webkitAudioContext;
if (AudioContext) {
    const originalCreateDynamicsCompressor = AudioContext.prototype.createDynamicsCompressor;
    AudioContext.prototype.createDynamicsCompressor = function() {
        const compressor = originalCreateDynamicsCompressor.call(this);
        compressor.reduce = function() {
            return originalReduce.call(this) + Math.random() * 0.0001;
        };
        return compressor;
    };
}
```
**Purpose**: Adds tiny variations to audio processing to prevent fingerprinting.

### 4. Human Mouse Movement
```python
# Lines 206-224 in HumanBehaviorSimulator
async def human_mouse_move(self, page: Page, x: int, y: int):
    """Move mouse in a human-like curved path"""
    steps = random.randint(15, 25)
    for i in range(steps):
        progress = i / steps
        curve_x = start_x + (x - start_x) * progress + random.randint(-5, 5)
        curve_y = start_y + (y - start_y) * progress + random.randint(-5, 5)
        await page.mouse.move(curve_x, curve_y)
        await asyncio.sleep(random.uniform(0.001, 0.003))
```
**Purpose**: Mimics human mouse movement patterns (not straight lines, variable speed).

### 5. Human Typing Patterns
```python
# Lines 226-247
async def human_type(self, page: Page, selector: str, text: str):
    base_delay = 60 / (self.typing_speed * 5)  # WPM-based
    for char in text:
        delay = base_delay * random.uniform(0.5, 2.0)
        if char in '.,!?;: ':
            delay *= random.uniform(1.5, 3.0)  # Pause at punctuation
        await page.keyboard.type(char)
        await asyncio.sleep(delay)
```
**Purpose**: Simulates realistic typing speed variations.

### 6. Adaptive Rate Limiting
```python
# Lines 357-379 in IntelligentRateLimit
def record_request(self, success: bool = True):
    if success:
        self.success_streak += 1
        self.backoff_multiplier = max(0.5, self.backoff_multiplier * 0.95)  # Speed up
    else:
        self.failure_streak += 1
        self.backoff_multiplier = min(5.0, self.backoff_multiplier * 1.5)  # Slow down
```
**Purpose**: Learns from successes/failures and adjusts request timing dynamically.

### 7. Session Health Monitoring
```python
# Lines 321-337
def is_healthy(self) -> bool:
    if self.error_count > 10:
        return False
    if self.time_since_last_activity() > 1800:  # 30 min
        return False
    if self.get_session_age() > 14400:  # 4 hours
        return False
    return True
```
**Purpose**: Detects session degradation before Twitter bans occur.

---

## SUCCESS CRITERIA

### Functional Requirements
- [ ] Initialize TwitterScraper without errors
- [ ] Authenticate to Twitter (reuse @iamcodio session)
- [ ] Scrape 10 tweets from @dankoe without detection
- [ ] Session persists across process restarts (cookies saved)
- [ ] All tweets normalized to UnifiedContent schema
- [ ] Health check returns accurate session status
- [ ] Rate limiting prevents burst requests
- [ ] Human behavior simulation active during scraping

### Integration Requirements
- [ ] TwitterScraper implements BaseScraper ABC
- [ ] `health_check()` returns proper dict structure
- [ ] `extract()` returns list of raw tweet dicts
- [ ] `normalize()` returns UnifiedContent Pydantic model
- [ ] `scrape()` combines extract + normalize correctly

### Data Quality
- [ ] Tweet content extracted accurately (no truncation)
- [ ] Engagement metrics (likes, retweets, replies) captured
- [ ] Timestamps parsed correctly (ISO format)
- [ ] Username/author info preserved
- [ ] Source URL constructed correctly
- [ ] Metadata includes hashtags, mentions, URLs

### Testing Commands
```bash
# Test basic import
python -c "from backend.scrapers import TwitterScraper; print('Import OK')"

# Test health check
python -c "
import asyncio
from backend.scrapers import TwitterScraper
async def test():
    s = TwitterScraper()
    await s.initialize()
    print(await s.health_check())
asyncio.run(test())
"

# Test scraping @dankoe
python -c "
import asyncio
from backend.scrapers.adapters.twitter import test_twitter_scraper
asyncio.run(test_twitter_scraper())
"
```

---

## CRITICAL WARNINGS

1. **DO NOT USE HEADLESS MODE**: Twitter detects headless browsers. Always use `headless=False`.

2. **DO NOT SKIP FINGERPRINT SPOOFING**: Remove ANY anti-detection code and you WILL be banned.

3. **DO NOT REMOVE RATE LIMITING**: Twitter will ban aggressive request patterns.

4. **DO NOT SIMPLIFY MOUSE MOVEMENTS**: Straight-line, instant movements are bot signatures.

5. **DO NOT HARDCODE CREDENTIALS**: Use environment variables from `.env`:
   ```
   TWITTER_HANDLE=iamcodio
   TWITTER_EMAIL=iamcodio37@gmail.com
   TWITTER_PASSWORD=<from secrets>
   CHROME_PROFILE=TweetHunter_Pro
   ```

6. **DO NOT REMOVE SESSION PERSISTENCE**: Re-authenticating for each scrape will trigger security alerts.

7. **PRESERVE ALL CHROME LAUNCH ARGUMENTS**: Each flag defeats a specific detection mechanism.

---

## ESTIMATED EFFORT

| Task | Time |
|------|------|
| Create directory structure | 5 min |
| Write BaseScraper ABC | 20 min |
| Copy and adapt _persistent_x_session.py | 30 min |
| Copy and adapt _playwright_oauth.py | 20 min |
| Write TwitterScraper wrapper | 45 min |
| Update pyproject.toml | 10 min |
| Install Playwright browsers | 10 min |
| Test initialization | 15 min |
| Test @dankoe scraping | 20 min |
| Verify data quality | 15 min |

**Total: 2-3 hours**

---

## NEXT AGENT (Gamma)

Once TwitterScraper is operational:
- Agent Gamma: YouTube Scraper (youtube-transcript-api integration)
- Agent Delta: Reddit Scraper (PRAW integration)
- Agent Epsilon: Web Scraper (Jina.ai + ScraperAPI)

---

## SUPPORT CONTACTS

- **Project Lead**: @iamcodio (GitHub)
- **IAC-024 Reference**: `/Users/kjd/01-projects/IAC-024-tweet-hunter/`
- **Architecture Docs**: `/Users/kjd/01-projects/IAC-032-unified-scraper/CLAUDE.md`

---

**Remember**: This is PROVEN CODE that successfully scrapes Twitter without bans. Your job is to WRAP it in the new interface, not to rewrite it. Trust the anti-detection mechanisms - they are battle-tested.

Good luck, Agent Beta.
