# PRD: Unified Multi-Platform Scraping Intelligence Engine
## IAC-032-unified-scraper | 3-Day MVP

**Last Updated:** Saturday, 15 Nov 2025 23:15 GMT  
**Deadline:** Tuesday EOD (3 days)  
**Budget:** €900 (expires Wednesday)

---

## Executive Summary

**What This Is:** Multi-platform web scraper with Tauri desktop interface that aggregates content from Twitter, YouTube, Reddit, Amazon, and 20+ other sources into a unified intelligence system. Outputs to markdown for your newsletter workflow.

**Based On:** Your 3+ hours of research into ScraperAPI architecture, Dan Koe methodology, and multi-platform intelligence engines.

**NOT:** Course indexer, Notion integration, PyQt desktop app.

---

## Architecture: Tauri + Rust + Python Modules

### Core Stack (From Your Research)

**Frontend:**
- **Tauri 2.0** - Rust-based desktop framework
- **Svelte 5** - Lightweight reactive UI
- 3-window layout: Research | Editor | Preview
- Async by default, native performance

**Backend Services (Python):**
- **ScraperAPI** ($49/mo, 100K credits) - Primary scraping
- **FastAPI** - REST API for Tauri to call
- **PostgreSQL + pgvector** - Unified content storage
- **ChromaDB** - Vector search for semantic queries
- **Redis + RQ** - Job queue for async scraping

**Package Management:**
- **UV** - Fast Python package manager
- **Cargo** - Rust dependencies

**Deployment:**
- **Podman** containers for services
- Desktop app runs locally

---

## Platform Coverage (From Research)

### Tier 1: MVP (Day 1-3)

**Twitter/X:**
- ScraperAPI structured endpoint
- Fallback: twscrape (free, requires accounts)
- IAC-024 Playwright OAuth patterns (you already built this)
- Extract: tweets, engagement, author, timestamp

**YouTube:**
- Bridge to existing youtube-intelligence-engine
- youtube-transcript-api for new videos
- Metadata: title, views, duration, chapters

**Reddit:**
- PRAW (free official API)
- Target: pain points, VOC language
- 1,000 requests per 10 min (OAuth authenticated)

**Amazon:**
- ScraperAPI structured endpoint ($0.0005/request)
- Focus: 1-3 star reviews (pain language)
- 5-star reviews (desire language)

### Tier 2: Week 2 (Post-MVP)

- LinkedIn (Lix API or scraping)
- Quora (question mining)
- ProductHunt (launch intelligence)
- Forums (phpBB, Discourse)
- Hacker News (Firebase API)
- Review sites (Trustpilot, G2)

---

## Unified Data Schema (From Research)

```json
{
  "content_id": "uuid",
  "platform": "twitter|youtube|reddit|amazon",
  "source_url": "https://...",
  "author": {
    "id": "string",
    "name": "string",
    "handle": "string"
  },
  "content": {
    "title": "string or null",
    "body": "string",
    "published_at": "ISO8601"
  },
  "metrics": {
    "engagement_score": 1234,
    "likes": 100,
    "shares": 50,
    "comments": 25
  },
  "analysis": {
    "hooks": ["extracted hooks"],
    "framework": "AIDA|PAS|BAB|PASTOR",
    "themes": ["productivity", "focus"],
    "sentiment": 0.85,
    "pain_points": [],
    "desires": []
  },
  "embedding": [0.123, ...],  // 1536 dimensions
  "scraped_at": "ISO8601",
  "metadata": {}
}
```

**Database Design:**

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    platform VARCHAR(50),
    source_url TEXT UNIQUE,
    author_id VARCHAR(255),
    content_title TEXT,
    content_body TEXT,
    published_at TIMESTAMP,
    metrics JSONB,
    analysis JSONB,
    embedding vector(1536),
    scraped_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_platform ON contents(platform);
CREATE INDEX idx_embedding ON contents USING ivfflat (embedding vector_cosine_ops);
```

---

## Tauri Desktop Architecture

### Window Structure

```
┌─────────────────────────────────────────────────────┐
│  Tauri Window (Rust + Svelte)                       │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │   Scraper    │   Markdown   │   Preview    │    │
│  │   Dashboard  │   Editor     │   Window     │    │
│  │              │              │              │    │
│  │ • Platforms  │ • Syntax HL  │ • Rendered   │    │
│  │ • Configs    │ • Word count │ • Export     │    │
│  │ • Queue      │ • Auto-save  │ • Hemingway  │    │
│  │ • Cards      │ • Citations  │ • HTML       │    │
│  └──────────────┴──────────────┴──────────────┘    │
└─────────────────────────────────────────────────────┘
                       ↓ IPC
            ┌──────────────────────┐
            │   FastAPI Backend    │
            │  (Python Services)   │
            ├──────────────────────┤
            │ • Scrapers           │
            │ • LLM Analysis       │
            │ • Vector Search      │
            │ • Job Queue          │
            └──────────────────────┘
```

### Tauri + Rust Benefits

**From your Rust/Tauri experience:**
- Small binary (~10MB vs 100MB+ Electron)
- Native file system access
- Async by default (Tokio runtime)
- Memory safe
- Fast startup (<1s vs 5s+ Electron)
- Plugin system for extensibility

**Tauri IPC Pattern:**

```rust
// Rust backend command
#[tauri::command]
async fn scrape_twitter(handle: String) -> Result<Vec<Tweet>, String> {
    // Call Python FastAPI service
    let response = reqwest::get(
        format!("http://localhost:8000/scrape/twitter?handle={}", handle)
    ).await?;
    
    response.json().await.map_err(|e| e.to_string())
}
```

```javascript
// Svelte frontend
import { invoke } from '@tauri-apps/api/tauri';

async function scrapeTwitter() {
    const tweets = await invoke('scrape_twitter', { 
        handle: 'dankoe' 
    });
    // Update UI with results
}
```

---

## Scraping Layer Architecture (From Research)

### ScraperAPI Integration

**Hobby Plan ($49/mo):**
- 100,000 API credits
- 20 concurrent threads
- Automatic CAPTCHA solving
- JavaScript rendering (+5 credits)
- Structured endpoints (Amazon, Google, eBay)
- 99.9% success rate
- No failed request charges

**Cost Breakdown:**
- Simple page: $0.00049 (2,040 pages per $1)
- JS-rendered: $0.0024 (417 pages per $1)
- 100K credits = ~20,000 pages/month

**Implementation:**

```python
# backend/scrapers/base.py
import requests

class ScraperAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.scraperapi.com"
    
    def fetch(self, url: str, render_js: bool = False):
        params = {
            "api_key": self.api_key,
            "url": url,
            "render": render_js
        }
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.text
```

### Platform Adapters (Modular)

**Adapter Pattern (from research):**

```python
# backend/scrapers/adapters/base.py
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def extract(self, url: str) -> dict:
        """Extract content from URL"""
        pass
    
    @abstractmethod
    def normalize(self, raw_data: dict) -> dict:
        """Normalize to unified schema"""
        pass
```

**Twitter Adapter (reuse IAC-024):**

```python
# backend/scrapers/adapters/twitter.py
class TwitterScraper(BaseScraper):
    def extract(self, url: str) -> dict:
        # Option 1: ScraperAPI
        if self.config['use_scraper_api']:
            html = scraper_api.fetch(url, render_js=True)
            return parse_twitter_html(html)
        
        # Option 2: IAC-024 Playwright OAuth
        elif self.config['use_playwright']:
            return self.playwright_scrape(url)
        
        # Option 3: twscrape (free)
        else:
            return self.twscrape_extract(url)
    
    def normalize(self, raw_data: dict) -> dict:
        return {
            "platform": "twitter",
            "content": {"body": raw_data['text']},
            "metrics": {
                "likes": raw_data['favorite_count'],
                "shares": raw_data['retweet_count']
            }
        }
```

---

## LLM Analysis Pipeline (From Research)

### Model Strategy

**MVP (OpenAI for testing):**
- GPT-4o: $0.0025/1K input, $0.01/1K output
- Fast, cheap for development
- Good for bulk processing

**Production (Claude Sonnet 4.5):**
- Best coding model in world
- Superior copywriting analysis
- $3/1M input, $15/1M output
- Use for final analysis, not scraping

**Model Router:**

```python
# backend/llm/router.py
class LLMRouter:
    def analyze_content(self, content: str, provider: str = "openai"):
        if provider == "openai":
            return self.openai_analyze(content)
        elif provider == "claude":
            return self.claude_analyze(content)
    
    def openai_analyze(self, content: str):
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"Extract copywriting frameworks from:\n{content}"
            }]
        )
        return response.choices[0].message.content
    
    def claude_analyze(self, content: str):
        # Claude Sonnet 4.5 API call
        response = anthropic.messages.create(
            model="claude-sonnet-4-5-20250929",
            messages=[{
                "role": "user",
                "content": f"Analyze this copy:\n{content}"
            }]
        )
        return response.content[0].text
```

### Analysis Types (From RMBC Research)

**Hook Extraction:**
- Curiosity-based hooks
- Specificity-based hooks (numbers, timeframes)
- Benefit-driven hooks
- Command hooks
- Question hooks

**Framework Detection:**
- AIDA (Attention, Interest, Desire, Action)
- PAS (Problem, Agitate, Solution)
- BAB (Before, After, Bridge)
- PASTOR (Problem, Amplify, Story, Transformation, Offer, Response)

**VOC Mining:**
- Pain points (1-3 star reviews)
- Desires (5-star reviews)
- Sentiment analysis (VADER)
- Customer language patterns

---

## Pattern Detection (From Research)

### Cross-Platform Pattern Algorithm

**Dan Koe's Workflow Pattern:**
1. Tweet concept (Tuesday)
2. Expand in newsletter (Saturday)
3. Create YouTube video (following week)

**Detection via Embeddings:**

```python
# backend/services/pattern_detector.py
def detect_elaboration_patterns(author_id: str, timeframe_days: int = 30):
    # Get all content for author
    contents = db.query("""
        SELECT id, platform, content_body, published_at, embedding
        FROM contents
        WHERE author_id = %s
        AND published_at > NOW() - INTERVAL '%s days'
    """, (author_id, timeframe_days))
    
    patterns = []
    
    # Compare each piece across platforms
    for c1 in contents:
        for c2 in contents:
            if c1.platform == c2.platform:
                continue
            
            # Cosine similarity via pgvector
            similarity = 1 - cosine_distance(c1.embedding, c2.embedding)
            
            if similarity > 0.85:  # High similarity threshold
                patterns.append({
                    "type": "elaboration",
                    "source": {
                        "platform": c1.platform,
                        "date": c1.published_at
                    },
                    "related": {
                        "platform": c2.platform,
                        "date": c2.published_at
                    },
                    "similarity": similarity,
                    "insight": f"Concept from {c1.platform} expanded to {c2.platform}"
                })
    
    return patterns
```

---

## Redis + RQ Job Queue (From Research)

### Why RQ Over Celery

**From research:**
- RQ: 15-minute learning curve
- Celery: 2-3 day learning curve
- RQ: Simple, Redis-only
- Perfect for 3-day deadline

**Queue Architecture:**

```python
# backend/queue/worker.py
from rq import Queue, Worker
from redis import Redis

redis_conn = Redis(host='localhost', port=6379)
queue = Queue('scraping', connection=redis_conn)

# Enqueue job
job = queue.enqueue(
    'scrapers.twitter_scraper.scrape',
    'https://twitter.com/dankoe/status/123',
    timeout='10m'
)

# Worker process
worker = Worker([queue], connection=redis_conn)
worker.work()
```

**Retry Logic with Tenacity:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def scrape_with_retry(url: str):
    response = scraper_api.fetch(url)
    return response
```

---

## Card System (Kortex-Style)

### Card Data Model

```python
# backend/models/card.py
class Card:
    id: UUID
    title: str
    body: str  # Markdown
    tags: List[str]
    source_url: str
    source_platform: str
    content_id: UUID  # FK to contents table
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    related_cards: List[UUID]  # Linked cards
    parent_card: Optional[UUID]  # Hierarchy
```

**Svelte Card Component:**

```svelte
<!-- frontend/src/components/Card.svelte -->
<script>
    export let card;
    
    async function addToEditor() {
        await invoke('insert_card_to_editor', { cardId: card.id });
    }
</script>

<div class="card" draggable="true">
    <header>
        <h3>{card.title}</h3>
        <button on:click={addToEditor}>→ Editor</button>
    </header>
    
    <div class="content">
        {@html marked(card.body)}
    </div>
    
    <footer>
        <div class="tags">
            {#each card.tags as tag}
                <span class="tag">{tag}</span>
            {/each}
        </div>
        <small>{card.source_platform} • {card.created_at}</small>
    </footer>
</div>
```

---

## Markdown Editor Integration

### Monaco Editor (VS Code Engine)

**Why Monaco:**
- Syntax highlighting built-in
- Auto-complete
- Multi-cursor editing
- Lightweight for Tauri

**Hemingway Analysis:**

```python
# backend/services/hemingway.py
from textstat import (
    flesch_kincaid_grade,
    passive_voice_ratio,
    difficult_words
)

def analyze_readability(text: str) -> dict:
    return {
        "grade_level": flesch_kincaid_grade(text),  # Target 6-8
        "passive_ratio": passive_voice_ratio(text),  # Target <10%
        "complex_words": difficult_words(text),
        "recommendations": generate_suggestions(text)
    }
```

---

## Export Pipeline

### Markdown → HTML (Astro)

**Project Structure:**

```
exports/
├── astro-site/
│   ├── src/
│   │   ├── content/
│   │   │   └── newsletters/
│   │   │       └── 2025-11-15-article.md
│   │   ├── layouts/
│   │   │   └── Newsletter.astro
│   │   └── pages/
│   └── astro.config.mjs
```

**Export Command (Tauri):**

```rust
#[tauri::command]
async fn export_markdown(content: String, filename: String) -> Result<String, String> {
    // Save to Astro content directory
    let path = format!("exports/astro-site/src/content/newsletters/{}.md", filename);
    std::fs::write(&path, content)
        .map_err(|e| e.to_string())?;
    
    // Trigger Astro build
    let output = tokio::process::Command::new("npm")
        .args(["run", "build"])
        .current_dir("exports/astro-site")
        .output()
        .await
        .map_err(|e| e.to_string())?;
    
    Ok(format!("Built to: dist/{}.html", filename))
}
```

---

## 3-Day Implementation Plan

### Day 1: Backend Core + Twitter

**Alpha Agent:**
- FastAPI scaffold
- PostgreSQL + pgvector setup
- ScraperAPI integration
- Twitter adapter (reuse IAC-024)
- Basic content storage

**Deliverable:** Can scrape 100 tweets, store in DB

### Day 2: Multi-Platform + Tauri Shell

**Beta Agent:**
- Reddit adapter (PRAW)
- Amazon adapter (ScraperAPI)
- YouTube bridge
- RQ job queue
- Tauri app shell (3 windows)

**Deliverable:** Desktop app opens, can queue scrape jobs

### Day 3: Analysis + Editor + Export

**Gamma Agent:**
- OpenAI analysis pipeline
- Card system (create, tag, link)
- Monaco editor integration
- Hemingway analysis
- Markdown → HTML export

**Deliverable:** Full workflow working

---

## Budget Breakdown

| Item | Cost/Month | Notes |
|------|------------|-------|
| ScraperAPI Hobby | $49 | 100K credits |
| OpenAI API | $20 | Testing only |
| PostgreSQL | $0 | Local or Hetzner VPS $4 |
| Redis | $0 | Local or free tier |
| ChromaDB | $0 | Local |
| **Total** | **$69/mo** | Under budget |

**3-Day Testing:**
- ScraperAPI: 5K credits used / 100K = 5%
- OpenAI: ~$5 for analysis
- Total: ~$54 spent

---

## Project Structure

```
IAC-032-unified-scraper/
├── backend/              # Python services
│   ├── scrapers/
│   │   ├── adapters/
│   │   │   ├── base.py
│   │   │   ├── twitter.py
│   │   │   ├── youtube.py
│   │   │   ├── reddit.py
│   │   │   └── amazon.py
│   │   └── scraper_api.py
│   ├── llm/
│   │   ├── router.py
│   │   ├── openai_client.py
│   │   └── claude_client.py
│   ├── services/
│   │   ├── pattern_detector.py
│   │   ├── hemingway.py
│   │   └── embeddings.py
│   ├── models/
│   │   ├── content.py
│   │   └── card.py
│   ├── api/
│   │   └── main.py  # FastAPI
│   └── queue/
│       └── worker.py  # RQ
├── frontend/            # Tauri + Svelte
│   ├── src/
│   │   ├── components/
│   │   │   ├── Card.svelte
│   │   │   ├── ScraperDashboard.svelte
│   │   │   ├── MarkdownEditor.svelte
│   │   │   └── Preview.svelte
│   │   ├── App.svelte
│   │   └── main.js
│   └── src-tauri/      # Rust backend
│       ├── src/
│       │   └── main.rs
│       └── Cargo.toml
├── exports/
│   └── astro-site/
└── docs/
    └── pm/
```

---

## Critical Path Dependencies

**Must complete in order:**

1. **FastAPI + PostgreSQL** (4 hours)
2. **ScraperAPI integration** (2 hours)
3. **Twitter adapter** (4 hours, reuse IAC-024)
4. **Tauri shell** (6 hours)
5. **Card system** (4 hours)
6. **Editor integration** (6 hours)
7. **Export pipeline** (3 hours)

**Total: ~29 hours across 3 days = doable with parallel agents**

---

## What's Different from PyQt Version

**OLD (PyQt - wrong):**
- ❌ Heavy Python GUI framework
- ❌ Slow startup
- ❌ Dated UI
- ❌ Single-threaded
- ❌ No native feel

**NEW (Tauri - correct):**
- ✅ Rust + Web tech
- ✅ Fast startup (<1s)
- ✅ Modern UI (Svelte)
- ✅ Async by default
- ✅ Native performance
- ✅ Your existing Rust experience

---

## Success Metrics

**Day 3 Deliverable:**
- [ ] Tauri app opens with 3 windows
- [ ] Scrape Twitter (100 tweets)
- [ ] Scrape Reddit (50 posts)
- [ ] Scrape Amazon reviews (20 products)
- [ ] YouTube bridge working
- [ ] Cards created from scraped content
- [ ] Markdown editor with syntax highlighting
- [ ] Export to HTML via Astro
- [ ] OpenAI analysis extracting frameworks

**Code Quality:**
- [ ] Modular adapters (easy to add platforms)
- [ ] Type-safe Rust IPC
- [ ] Clean separation: Tauri ← FastAPI ← Scrapers
- [ ] RQ queue handling async scraping
- [ ] PostgreSQL storing unified schema

---

**This PRD is based on YOUR research. Not my assumptions. Ready to hand to Claude Code for implementation.**
