# Research Guide: Content Scraping & Intelligence

Complete guide to using the Extrophi Research backend for multi-platform content scraping, semantic search, LLM analysis, and content intelligence. Turn raw social media content into actionable insights.

---

## Table of Contents

1. [What is Research?](#what-is-research)
2. [Installation & Setup](#installation--setup)
3. [Scraping Platforms](#scraping-platforms)
4. [Semantic Search (RAG)](#semantic-search-rag)
5. [LLM Analysis](#llm-analysis)
6. [Pattern Detection](#pattern-detection)
7. [Content Generation](#content-generation)
8. [API Reference](#api-reference)
9. [Workflow Examples](#workflow-examples)
10. [Troubleshooting](#troubleshooting)

---

## What is Research?

**Extrophi Research** is a multi-platform content intelligence engine for content creators, copywriters, and marketers. It scrapes Twitter, YouTube, Reddit, and web content, then uses AI to extract insights, detect patterns, and generate content.

### Core Features

✅ **Multi-Platform Scraping**: Twitter, YouTube, Reddit, Amazon, blogs
✅ **Semantic Search**: RAG-powered queries with ChromaDB + pgvector
✅ **LLM Analysis**: OpenAI GPT-4 for bulk analysis, Claude Sonnet for polish
✅ **Framework Detection**: Auto-identifies AIDA, PAS, BAB, PASTOR in content
✅ **Pattern Recognition**: Detects cross-platform elaboration (tweet → video → course)
✅ **Content Generation**: Course scripts, content briefs, tweet threads

### Use Cases

**Content Creators:**
- Research any topic by analyzing top creators
- Find content gaps and opportunities
- Detect what formats work best on each platform

**Copywriters:**
- Extract proven frameworks from successful content
- Mine authentic customer language from reviews
- Identify high-performing hooks and angles

**Marketers:**
- Authority ranking (who are the top voices?)
- Competitive analysis (what's working for competitors?)
- Trend detection (what topics are gaining traction?)

---

## Installation & Setup

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 16** with pgvector extension
- **Redis** (for job queue)
- **UV** package manager (not pip!)
- **API Keys**: OpenAI, ScraperAPI (optional)

### Step 1: Install System Dependencies

**macOS:**
```bash
# Install PostgreSQL with pgvector
brew install postgresql@16 pgvector redis

# Start services
brew services start postgresql@16
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
# PostgreSQL + pgvector
sudo apt install postgresql-16 postgresql-16-pgvector redis-server

# Start services
sudo systemctl start postgresql redis-server
```

### Step 2: Clone Repository

```bash
git clone https://github.com/extrophi/extrophi-ecosystem.git
cd extrophi-ecosystem/research/backend
```

### Step 3: Setup Python Environment

**IMPORTANT: Use UV, not pip!**

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Step 4: Database Setup

```bash
# Create database
createdb unified_scraper

# Enable pgvector extension
psql unified_scraper -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations (creates tables)
python -m backend.db.migrate
```

**Database Schema:**
- `contents` - Scraped content from all platforms
- `embeddings` - Vector embeddings for semantic search
- `users` - User accounts
- `cards` - Published cards from Writer
- `attributions` - Citations, remixes, replies
- `extropy_ledger` - Token transaction history

### Step 5: Environment Variables

Create `.env` file in `research/backend/`:

```bash
# Database
DATABASE_URL=postgresql://localhost:5432/unified_scraper

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI (required for embeddings and analysis)
OPENAI_API_KEY=sk-...

# Anthropic Claude (optional, for copywriting polish)
ANTHROPIC_API_KEY=sk-ant-...

# ScraperAPI (optional, for web scraping)
SCRAPER_API_KEY=...

# Jina.ai (optional, free tier needs no key)
# JINA_API_KEY=...  # Only if using paid tier
```

**Cost Breakdown:**
- OpenAI: ~$20/month (embeddings + GPT-4 analysis)
- ScraperAPI: $49/month (100K credits, 20K pages)
- Claude: ~$10/month (Sonnet for polish)
- PostgreSQL/Redis: Free (self-hosted)

### Step 6: Start API Server

```bash
# Development mode (with hot reload)
uvicorn backend.main:app --reload --port 8000

# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Verify it's running:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "openai": "configured"
  }
}
```

---

## Scraping Platforms

### Twitter Scraping

**Endpoint:** `POST /scrape/twitter`

**Features:**
- OAuth-authenticated scraping (no rate limits)
- Human behavior simulation (anti-bot evasion)
- Profile scraping (bio, followers, tweets)
- Thread scraping (entire thread context)

**Example:**
```bash
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "username": "naval",
    "max_tweets": 100,
    "include_replies": false,
    "include_retweets": false
  }'
```

**Response:**
```json
{
  "scraped": 100,
  "stored": 100,
  "errors": 0,
  "username": "naval",
  "content_ids": ["uuid-1", "uuid-2", ...]
}
```

**Stored Data:**
- Tweet text, author, metrics (likes, retweets)
- Thread context (if part of thread)
- Media URLs (images, videos)
- Engagement score (calculated)

**Rate Limits:**
- OAuth method: ~3,000 tweets/hour
- Uses IAC-024 battle-tested scraper

### YouTube Scraping

**Endpoint:** `POST /scrape/youtube`

**Features:**
- Transcript extraction (youtube-transcript-api)
- Video metadata (title, description, views)
- Channel analysis
- Comment scraping (top comments)

**Example:**
```bash
curl -X POST http://localhost:8000/scrape/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "include_comments": true,
    "max_comments": 100
  }'
```

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "transcript_length": 1234,
  "comments_scraped": 100,
  "content_id": "uuid-1"
}
```

**Stored Data:**
- Full transcript with timestamps
- Video metadata (views, likes, publish date)
- Top comments (sorted by likes)
- Channel info (subscribers, videos)

**Rate Limits:**
- No rate limits (uses public transcript API)
- ~600 videos/hour

### Reddit Scraping

**Endpoint:** `POST /scrape/reddit`

**Features:**
- Subreddit scraping (top posts, hot posts)
- Comment tree extraction (nested comments)
- User analysis (karma, post history)
- Pain point detection (from complaints)

**Example:**
```bash
curl -X POST http://localhost:8000/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit": "Entrepreneur",
    "sort_by": "top",
    "time_filter": "week",
    "max_posts": 50
  }'
```

**Response:**
```json
{
  "subreddit": "Entrepreneur",
  "posts_scraped": 50,
  "comments_scraped": 250,
  "content_ids": ["uuid-1", "uuid-2", ...]
}
```

**Stored Data:**
- Post title, body, author, score
- Top comments (with score, replies)
- Subreddit metadata (subscribers, description)
- Pain language detected (complaints, frustrations)

**Rate Limits:**
- PRAW official API: 60 requests/minute
- ~1,000 posts/hour

### Web Scraping

**Endpoint:** `POST /scrape/web`

**Features:**
- Any URL scraping (Jina.ai Reader API)
- HTML → Markdown conversion
- ScraperAPI fallback for complex sites
- Blog post extraction

**Example:**
```bash
curl -X POST http://localhost:8000/scrape/web \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/blog/post",
    "extract_links": true,
    "follow_links": false
  }'
```

**Response:**
```json
{
  "url": "https://example.com/blog/post",
  "title": "Blog Post Title",
  "word_count": 1500,
  "links_extracted": 15,
  "content_id": "uuid-1"
}
```

**Stored Data:**
- Markdown-formatted content
- Extracted metadata (title, author, date)
- Outbound links
- Images and media

**Rate Limits:**
- Jina.ai Free: 50K pages/month
- ScraperAPI: 100K credits/month ($49 plan)

---

## Semantic Search (RAG)

RAG (Retrieval Augmented Generation) enables semantic search across all scraped content using vector embeddings.

### How It Works

1. **Content Scraped** → Stored in PostgreSQL
2. **OpenAI Embeddings** → Generate 1536-dimensional vectors
3. **ChromaDB + pgvector** → Store vectors for fast search
4. **Query** → Convert query to vector, find similar content
5. **GPT-4** → Synthesize results into answer

### Basic Semantic Search

**Endpoint:** `POST /query/semantic`

**Example:**
```bash
curl -X POST http://localhost:8000/query/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do content creators grow their audience?",
    "platforms": ["twitter", "youtube"],
    "limit": 10
  }'
```

**Response:**
```json
{
  "query": "How do content creators grow their audience?",
  "results": [
    {
      "content_id": "uuid-1",
      "platform": "twitter",
      "text": "The key to growing on Twitter: 1) Post daily...",
      "author": "naval",
      "similarity": 0.89,
      "url": "https://twitter.com/naval/status/..."
    },
    ...
  ],
  "total_results": 10
}
```

### Advanced Semantic Search

**Filter by Platform:**
```json
{
  "query": "content marketing strategies",
  "platforms": ["youtube"],  // Only search YouTube
  "limit": 20
}
```

**Filter by Date:**
```json
{
  "query": "AI trends",
  "date_from": "2025-01-01",
  "date_to": "2025-11-18",
  "limit": 50
}
```

**Filter by Engagement:**
```json
{
  "query": "viral tweets",
  "min_engagement_score": 1000,  // Only highly-engaged content
  "platforms": ["twitter"],
  "limit": 10
}
```

### RAG Answer Generation

**Endpoint:** `POST /query/rag-answer`

**Example:**
```bash
curl -X POST http://localhost:8000/query/rag-answer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the best hooks for Twitter threads?",
    "context_limit": 10,
    "synthesize": true
  }'
```

**Response:**
```json
{
  "query": "What are the best hooks for Twitter threads?",
  "answer": "Based on analyzing 100+ viral threads, the best hooks are:\n\n1. **Curiosity-based**: 'I spent $10K testing X so you don't have to...'\n2. **Specificity**: '7 psychological triggers that made me $1M...'\n3. **Contrarian**: 'Everyone tells you to X, but here's why Y works better...'\n\nSources: @naval, @dickiebush, @thedankoe",
  "sources": [
    {"author": "naval", "url": "...", "excerpt": "..."},
    ...
  ],
  "confidence": 0.92
}
```

**What happens:**
1. Query converted to embedding
2. Top 10 similar content pieces retrieved
3. GPT-4 synthesizes answer from sources
4. Cites original sources

---

## LLM Analysis

Use OpenAI GPT-4 and Claude Sonnet to analyze scraped content, extract frameworks, and identify patterns.

### Framework Detection

**Endpoint:** `POST /analyze/frameworks`

Automatically detects copywriting frameworks in content:
- **AIDA**: Attention, Interest, Desire, Action
- **PAS**: Problem, Agitate, Solution
- **BAB**: Before, After, Bridge
- **PASTOR**: Problem, Amplify, Story, Transformation, Offer, Response

**Example:**
```bash
curl -X POST http://localhost:8000/analyze/frameworks \
  -H "Content-Type: application/json" \
  -d '{
    "content_ids": ["uuid-1", "uuid-2", "uuid-3"],
    "frameworks": ["aida", "pas", "bab"]
  }'
```

**Response:**
```json
{
  "analyzed": 3,
  "results": [
    {
      "content_id": "uuid-1",
      "frameworks_detected": ["aida", "pas"],
      "breakdown": {
        "aida": {
          "attention": "Hook about $10K mistake",
          "interest": "Explains common problem",
          "desire": "Shows transformation",
          "action": "Clear CTA at end"
        }
      }
    }
  ]
}
```

### Hook Extraction

**Endpoint:** `POST /analyze/hooks`

Extracts high-performing hooks from content:

**Example:**
```bash
curl -X POST http://localhost:8000/analyze/hooks \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "twitter",
    "min_engagement_score": 1000,
    "limit": 50
  }'
```

**Response:**
```json
{
  "hooks": [
    {
      "text": "I spent $10K testing X so you don't have to",
      "type": "curiosity",
      "engagement_score": 5420,
      "author": "@username",
      "url": "..."
    },
    {
      "text": "7 psychological triggers that made me $1M",
      "type": "specificity",
      "engagement_score": 4890,
      "author": "@username",
      "url": "..."
    }
  ]
}
```

**Hook Types:**
- **Curiosity**: Creates information gap
- **Specificity**: Uses numbers, data
- **Contrarian**: Challenges common beliefs
- **Benefit-driven**: Clear value proposition
- **Story**: Personal narrative

### Authority Ranking

**Endpoint:** `GET /analyze/authorities`

Identifies top creators in a niche:

**Example:**
```bash
curl "http://localhost:8000/analyze/authorities?topic=content+marketing&platform=twitter&limit=20"
```

**Response:**
```json
{
  "topic": "content marketing",
  "platform": "twitter",
  "authorities": [
    {
      "username": "@dickiebush",
      "authority_score": 95,
      "metrics": {
        "followers": 450000,
        "avg_engagement": 2500,
        "content_quality": 0.92,
        "consistency": 0.88
      },
      "top_content": ["tweet-id-1", "tweet-id-2"]
    }
  ]
}
```

**Authority Score Algorithm:**
```
authority_score = (
  followers * 0.2 +
  avg_engagement * 0.3 +
  content_quality * 0.3 +
  consistency * 0.2
)
```

---

## Pattern Detection

Detect cross-platform content patterns—how creators repurpose content across Twitter, YouTube, newsletters, and courses.

### Cross-Platform Elaboration

**Endpoint:** `POST /analyze/patterns`

Detects when a creator elaborates the same idea across platforms:

**Example:**
```bash
curl -X POST http://localhost:8000/analyze/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "author": "@thedankoe",
    "platforms": ["twitter", "youtube"],
    "min_similarity": 0.7
  }'
```

**Response:**
```json
{
  "author": "@thedankoe",
  "patterns_detected": [
    {
      "core_idea": "Build audience before product",
      "elaborations": [
        {
          "platform": "twitter",
          "format": "tweet",
          "length": "280 chars",
          "engagement": 1200,
          "url": "..."
        },
        {
          "platform": "twitter",
          "format": "thread",
          "length": "2500 words",
          "engagement": 3400,
          "url": "..."
        },
        {
          "platform": "youtube",
          "format": "video",
          "length": "15 minutes",
          "views": 45000,
          "url": "..."
        }
      ],
      "similarity": 0.85
    }
  ]
}
```

**Pattern Insights:**
1. Atomic idea on Twitter (test reaction)
2. Thread elaboration if engagement is good
3. YouTube video if thread performs well
4. Newsletter/course if video gets traction

**Use Case:** Reverse-engineer how top creators build content funnels.

### Content Gap Analysis

**Endpoint:** `POST /analyze/gaps`

Identifies topics that competitors haven't covered yet:

**Example:**
```bash
curl -X POST http://localhost:8000/analyze/gaps \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "content marketing",
    "competitors": ["@dickiebush", "@thedankoe", "@heyblake"],
    "market_size": "all"
  }'
```

**Response:**
```json
{
  "topic": "content marketing",
  "gaps_identified": [
    {
      "subtopic": "Content repurposing for YouTube Shorts",
      "search_volume": "high",
      "competition": "low",
      "covered_by": 0,
      "opportunity_score": 92
    },
    {
      "subtopic": "AI-assisted content workflows",
      "search_volume": "medium",
      "competition": "medium",
      "covered_by": 1,
      "opportunity_score": 78
    }
  ]
}
```

**Use Case:** Find white space opportunities in saturated markets.

---

## Content Generation

Generate production-ready content from scraped data and analysis.

### Course Script Generator

**Endpoint:** `POST /generate/course-script`

Generates course outlines and scripts from scraped content:

**Example:**
```bash
curl -X POST http://localhost:8000/generate/course-script \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How to grow on Twitter",
    "sources": ["uuid-1", "uuid-2", "uuid-3"],
    "modules": 5,
    "lessons_per_module": 4,
    "depth": "comprehensive"
  }'
```

**Response:**
```json
{
  "course_title": "Twitter Growth Accelerator",
  "modules": [
    {
      "module_number": 1,
      "title": "Foundation: Profile Optimization",
      "lessons": [
        {
          "lesson_number": 1,
          "title": "Crafting Your Bio for Discovery",
          "duration": "12 minutes",
          "script": "In this lesson, we'll...",
          "key_points": ["...", "..."],
          "action_items": ["...", "..."],
          "citations": [
            {"author": "@naval", "url": "..."}
          ]
        }
      ]
    }
  ]
}
```

**Output Format:** Markdown with full course structure.

### Content Brief Generator

**Endpoint:** `POST /generate/brief`

Creates research-backed content briefs for blog posts, newsletters, or videos:

**Example:**
```bash
curl -X POST http://localhost:8000/generate/brief \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Content marketing trends 2025",
    "format": "blog_post",
    "word_count": 2000,
    "include_stats": true
  }'
```

**Response:**
```json
{
  "title": "7 Content Marketing Trends Dominating 2025",
  "subtitle": "Based on analyzing 10,000+ pieces of content from top creators",
  "outline": [
    {
      "section": "Introduction",
      "key_points": ["Hook", "Why this matters", "What you'll learn"],
      "word_count": 150
    },
    {
      "section": "Trend 1: AI-Assisted Creation",
      "key_points": ["Stats", "Examples", "Implementation"],
      "word_count": 300,
      "sources": [{"author": "@username", "url": "..."}]
    }
  ],
  "seo_keywords": ["content marketing", "2025 trends", "..."],
  "call_to_action": "Try these strategies in your next campaign"
}
```

### Tweet Thread Generator

**Endpoint:** `POST /generate/thread`

Converts long-form content into Twitter threads:

**Example:**
```bash
curl -X POST http://localhost:8000/generate/thread \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "uuid-1",
    "max_tweets": 10,
    "style": "educational"
  }'
```

**Response:**
```json
{
  "thread": [
    {
      "tweet_number": 1,
      "text": "I spent $10K testing content marketing strategies so you don't have to.\n\nHere are the 7 that actually work in 2025:\n\n🧵 (thread)",
      "char_count": 156
    },
    {
      "tweet_number": 2,
      "text": "1/ AI-Assisted Creation\n\nStop treating AI as a replacement. Use it as a research assistant.\n\n• Scrape competitor content\n• Extract frameworks\n• Generate 10 angles\n• You write the final draft",
      "char_count": 210
    }
  ]
}
```

**Styles:**
- `educational`: Teaching, how-to
- `storytelling`: Personal narrative
- `contrarian`: Challenge beliefs
- `data-driven`: Stats and research

---

## API Reference

### Authentication

All API endpoints require an API key:

```bash
curl -X POST http://localhost:8000/scrape/twitter \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Get API Key:**
```bash
# Create user account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourusername",
    "email": "you@example.com",
    "password": "your-secure-password"
  }'

# Get API key
curl -X POST http://localhost:8000/auth/api-key \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourusername",
    "password": "your-secure-password"
  }'
```

### Endpoints Summary

**Scraping:**
- `POST /scrape/twitter` - Scrape Twitter profile/tweets
- `POST /scrape/youtube` - Scrape YouTube video/transcript
- `POST /scrape/reddit` - Scrape subreddit posts
- `POST /scrape/web` - Scrape any URL

**Querying:**
- `POST /query/semantic` - Semantic search
- `POST /query/rag-answer` - RAG answer generation

**Analysis:**
- `POST /analyze/frameworks` - Detect copywriting frameworks
- `POST /analyze/hooks` - Extract hooks
- `GET /analyze/authorities` - Authority ranking
- `POST /analyze/patterns` - Cross-platform patterns
- `POST /analyze/gaps` - Content gap analysis

**Generation:**
- `POST /generate/course-script` - Course script
- `POST /generate/brief` - Content brief
- `POST /generate/thread` - Tweet thread

**Full API Docs:** Visit `http://localhost:8000/docs` (Swagger UI)

---

## Workflow Examples

### Content Creator Research Workflow

**Goal:** Research a topic comprehensively before creating content.

**Step 1: Scrape Authorities (30 min)**
```bash
# Scrape top 10 creators in your niche
for username in naval dickiebush thedankoe; do
  curl -X POST http://localhost:8000/scrape/twitter \
    -H "X-API-Key: $API_KEY" \
    -d "{\"username\": \"$username\", \"max_tweets\": 100}"
done
```

**Step 2: Semantic Search (5 min)**
```bash
# Find all content about your specific topic
curl -X POST http://localhost:8000/query/semantic \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "query": "how to grow audience from zero",
    "platforms": ["twitter", "youtube"],
    "limit": 50
  }' > research-results.json
```

**Step 3: Framework Analysis (10 min)**
```bash
# Identify proven frameworks
curl -X POST http://localhost:8000/analyze/frameworks \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "content_ids": ["..."],  # IDs from step 2
    "frameworks": ["aida", "pas", "bab"]
  }' > frameworks.json
```

**Step 4: Generate Content Brief (2 min)**
```bash
# Create research-backed outline
curl -X POST http://localhost:8000/generate/brief \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "topic": "grow audience from zero",
    "format": "video_script",
    "duration": 15
  }' > content-brief.json
```

**Time:** 47 minutes
**Output:** Comprehensive research + content brief

### Competitive Intelligence Workflow

**Goal:** Analyze competitors' content strategies.

**Step 1: Scrape Competitors**
```bash
# Scrape 3 competitors (all platforms)
for competitor in competitor1 competitor2 competitor3; do
  # Twitter
  curl -X POST http://localhost:8000/scrape/twitter ...
  # YouTube
  curl -X POST http://localhost:8000/scrape/youtube ...
done
```

**Step 2: Pattern Detection**
```bash
# Detect cross-platform strategies
curl -X POST http://localhost:8000/analyze/patterns \
  -d '{
    "author": "competitor1",
    "platforms": ["twitter", "youtube", "newsletter"]
  }'
```

**Step 3: Gap Analysis**
```bash
# Find opportunities they're missing
curl -X POST http://localhost:8000/analyze/gaps \
  -d '{
    "topic": "your niche",
    "competitors": ["competitor1", "competitor2", "competitor3"]
  }'
```

**Output:** Complete competitive analysis + opportunity map

### Authority Building Workflow

**Goal:** Study and replicate top creators' strategies.

**Step 1: Identify Authorities**
```bash
curl "http://localhost:8000/analyze/authorities?topic=your-niche&limit=20"
```

**Step 2: Deep Dive on Top 3**
```bash
# Scrape everything from top 3 authorities
# Analyze their frameworks, hooks, patterns
```

**Step 3: Generate Your Content**
```bash
# Use their frameworks to create your own unique content
curl -X POST http://localhost:8000/generate/thread \
  -d '{
    "topic": "your unique angle",
    "style": "educational",
    "frameworks": ["aida", "pas"]
  }'
```

---

## Troubleshooting

### Scraping Issues

**Problem: Twitter scraper fails with "Authentication error"**
- Check if Chrome profile exists: `~/Library/Application Support/Google/Chrome/`
- Re-run OAuth flow
- Verify cookies haven't expired

**Problem: YouTube transcript not found**
- Some videos don't have transcripts (music, shorts)
- Try different video ID
- Check if captions are enabled on YouTube

**Problem: Reddit scraper hitting rate limits**
- PRAW has 60 req/min limit
- Add delays between requests
- Use multiple Reddit accounts

### Database Issues

**Problem: pgvector extension not found**
```sql
-- Install pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Problem: Slow semantic search**
```sql
-- Create index on embeddings
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

### LLM Issues

**Problem: OpenAI rate limit exceeded**
- Upgrade to Tier 2 ($50 spent): 10K req/min
- Add retry logic with exponential backoff
- Batch requests when possible

**Problem: Claude API timeout**
- Reduce max_tokens (default: 4096)
- Use GPT-4 for bulk processing, Claude for final polish

---

## Resources

- **API Guide**: [./api-guide.md](./api-guide.md) - Authentication, endpoints, SDKs
- **Writer Guide**: [./writer-guide.md](./writer-guide.md) - Voice journaling workflow
- **GitHub**: [github.com/extrophi/extrophi-ecosystem](https://github.com/extrophi/extrophi-ecosystem)
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)

---

**Built for content creators who research deeply and create strategically.**

🌐 Scrape → 🧠 Analyze → 📊 Detect → 🎯 Create
