# API Endpoint Specifications - IAC-032 Unified Scraper

**Framework**: FastAPI (Python 3.11+)
**Base URL**: `http://localhost:8000` (dev), `https://api.unifiedscraper.com` (prod)
**Authentication**: API key (header: `X-API-Key`)

---

## Table of Contents

1. [Scraping Endpoints](#scraping-endpoints)
2. [Query & Search Endpoints](#query--search-endpoints)
3. [Analysis Endpoints](#analysis-endpoints)
4. [Pattern Detection Endpoints](#pattern-detection-endpoints)
5. [Content Generation Endpoints](#content-generation-endpoints)
6. [Export Endpoints](#export-endpoints)
7. [Admin & Health Endpoints](#admin--health-endpoints)

---

## Scraping Endpoints

### POST `/scrape`

**Universal scraping endpoint** - Platform-agnostic content scraping.

**Request Body**:
```json
{
  "platform": "twitter",
  "target": "dankoe",  // username, URL, subreddit, video ID
  "scrape_type": "user_timeline",  // user_timeline, search, single_post, reviews
  "limit": 100,
  "options": {
    "include_replies": false,
    "min_engagement": 100
  }
}
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "estimated_time_seconds": 120,
  "message": "Scraping job queued for processing"
}
```

**Status Codes**:
- `202 Accepted`: Job queued successfully
- `400 Bad Request`: Invalid platform or parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Scraping failed

---

### POST `/scrape/twitter`

**Twitter-specific scraping** with advanced options.

**Request Body**:
```json
{
  "username": "dankoe",
  "limit": 100,
  "scrape_type": "timeline",  // timeline, search, thread
  "filters": {
    "min_likes": 1000,
    "has_media": true,
    "exclude_replies": true,
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  },
  "use_oauth": false  // Use persistent session (default) or OAuth fallback
}
```

**Response**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": {
    "total_expected": 100,
    "scraped": 0,
    "stored": 0
  }
}
```

---

### POST `/scrape/youtube`

**YouTube video/channel scraping**.

**Request Body**:
```json
{
  "target": "dQw4w9WgXcQ",  // video ID or channel ID
  "scrape_type": "video",  // video, channel, playlist
  "include_transcript": true,
  "include_comments": false,
  "comment_limit": 100
}
```

**Response**:
```json
{
  "job_id": "uuid",
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "duration_seconds": 213,
  "transcript_available": true
}
```

---

### POST `/scrape/reddit`

**Reddit subreddit/post scraping**.

**Request Body**:
```json
{
  "subreddit": "productivity",
  "scrape_type": "hot",  // hot, top, new, rising
  "limit": 50,
  "timeframe": "week",  // hour, day, week, month, year, all
  "include_comments": true,
  "comment_depth": 2
}
```

---

### POST `/scrape/amazon`

**Amazon product review scraping**.

**Request Body**:
```json
{
  "asin": "B08XYZ123",
  "scrape_type": "reviews",
  "filters": {
    "star_rating": [1, 2, 3],  // 1-3 stars for pain points
    "verified_only": true,
    "sort_by": "helpful"  // helpful, recent
  },
  "limit": 100
}
```

---

### GET `/scrape/jobs/{job_id}`

**Check scraping job status**.

**Response**:
```json
{
  "job_id": "uuid",
  "status": "completed",  // queued, processing, completed, failed
  "progress": {
    "total_expected": 100,
    "scraped": 100,
    "stored": 98,
    "failed": 2
  },
  "results": {
    "content_ids": ["uuid1", "uuid2", ...],
    "summary": {
      "platform": "twitter",
      "total_scraped": 100,
      "avg_engagement": 1234,
      "viral_count": 15
    }
  },
  "started_at": "2025-01-15T14:30:00Z",
  "completed_at": "2025-01-15T14:32:15Z",
  "duration_seconds": 135
}
```

---

## Query & Search Endpoints

### POST `/query/rag`

**Semantic RAG query** across all scraped content.

**Request Body**:
```json
{
  "prompt": "What does Dan Koe say about focus systems?",
  "filters": {
    "platforms": ["twitter", "youtube"],
    "authors": ["dankoe"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2025-01-31"
    },
    "min_engagement": 500
  },
  "limit": 10,
  "include_context": true
}
```

**Response**:
```json
{
  "query": "What does Dan Koe say about focus systems?",
  "results": [
    {
      "content_id": "uuid",
      "platform": "twitter",
      "author": "Dan Koe",
      "body": "Your focus determines your reality...",
      "source_url": "https://twitter.com/dankoe/status/123",
      "similarity_score": 0.92,
      "metrics": {"likes": 1234, "engagement_rate": 0.045},
      "published_at": "2025-01-15T14:30:00Z"
    }
  ],
  "summary": {
    "total_results": 47,
    "returned": 10,
    "avg_similarity": 0.85,
    "platforms": {"twitter": 32, "youtube": 15}
  }
}
```

---

### GET `/search`

**Traditional keyword search** with filters.

**Query Parameters**:
- `q`: Search query (required)
- `platform`: Filter by platform
- `author`: Filter by author
- `limit`: Results limit (default: 20)
- `offset`: Pagination offset

**Response**:
```json
{
  "query": "focus systems",
  "results": [...],  // Similar to RAG results
  "pagination": {
    "total": 487,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

### POST `/search/similar`

**Find content similar to a given piece**.

**Request Body**:
```json
{
  "content_id": "uuid",  // or provide text directly
  "text": "Your focus determines your reality",
  "limit": 10,
  "filters": {
    "exclude_platform": "twitter",  // Find similar on OTHER platforms
    "same_author_only": false
  }
}
```

---

## Analysis Endpoints

### POST `/analyze/content`

**LLM analysis of scraped content**.

**Request Body**:
```json
{
  "content_ids": ["uuid1", "uuid2"],
  "analysis_types": [
    "framework_detection",  // AIDA, PAS, BAB, PASTOR
    "hook_extraction",
    "sentiment_analysis",
    "theme_extraction",
    "viral_prediction"
  ],
  "llm_provider": "openai",  // openai, anthropic
  "llm_model": "gpt-4o"
}
```

**Response**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "content_count": 2,
  "estimated_cost_usd": 0.024
}
```

---

### GET `/analyze/jobs/{job_id}`

**Check analysis job status**.

**Response**:
```json
{
  "job_id": "uuid",
  "status": "completed",
  "results": [
    {
      "content_id": "uuid",
      "analyses": [
        {
          "type": "framework_detection",
          "result": {
            "frameworks": ["AIDA"],
            "breakdown": {
              "attention": "Your focus determines your reality",
              "interest": "Here's how to build...",
              "desire": "unbreakable focus systems",
              "action": "Thread below 👇"
            },
            "confidence": 0.92
          },
          "tokens_used": 234,
          "cost_usd": 0.000587
        }
      ]
    }
  ],
  "total_cost_usd": 0.024
}
```

---

### GET `/analyze/authority/{author_id}`

**Calculate author authority score**.

**Response**:
```json
{
  "author": {
    "id": "dankoe",
    "name": "Dan Koe",
    "platforms": ["twitter", "youtube"]
  },
  "authority_score": 92.5,
  "breakdown": {
    "follower_score": 95.0,  // 30% weight
    "engagement_score": 88.0,  // 40% weight
    "content_quality_score": 94.0  // 30% weight
  },
  "metrics": {
    "total_content": 1547,
    "viral_content": 234,
    "avg_engagement_rate": 0.044,
    "total_followers": 450000
  },
  "ranking": {
    "global": 12,
    "in_niche": 3  // "productivity" niche
  }
}
```

---

## Pattern Detection Endpoints

### POST `/patterns/detect`

**Detect cross-platform content patterns**.

**Request Body**:
```json
{
  "author_id": "dankoe",
  "pattern_types": [
    "elaboration",  // Tweet → Newsletter → Video
    "repurposing",  // Same content, multiple platforms
    "thread_to_video",
    "test_and_expand"  // Viral tweet → Full content
  ],
  "timeframe_days": 30,
  "min_similarity": 0.85
}
```

**Response**:
```json
{
  "patterns": [
    {
      "id": "uuid",
      "pattern_type": "elaboration",
      "description": "Tweet concept expanded to YouTube video",
      "source": {
        "content_id": "uuid",
        "platform": "twitter",
        "body": "Focus systems thread...",
        "published_at": "2025-01-10"
      },
      "related": [
        {
          "content_id": "uuid",
          "platform": "youtube",
          "title": "How to Build Unbreakable Focus",
          "published_at": "2025-01-17"
        }
      ],
      "similarity": 0.91,
      "temporal_gap_days": 7,
      "insights": {
        "expansion_ratio": 4.2,  // Video 4.2x longer than tweet
        "engagement_lift": 2.3,  // Video got 2.3x more engagement
        "platforms_used": ["twitter", "youtube"]
      },
      "confidence": 0.94
    }
  ],
  "summary": {
    "total_patterns": 47,
    "by_type": {
      "elaboration": 23,
      "repurposing": 15,
      "test_and_expand": 9
    }
  }
}
```

---

### GET `/patterns/timeline/{author_id}`

**Visualize content pattern timeline**.

**Response**:
```json
{
  "author": "Dan Koe",
  "timeline": [
    {
      "date": "2025-01-10",
      "content": [
        {"platform": "twitter", "content_id": "uuid", "type": "tweet"}
      ]
    },
    {
      "date": "2025-01-17",
      "content": [
        {"platform": "youtube", "content_id": "uuid", "type": "video"},
        {"platform": "newsletter", "content_id": "uuid", "type": "article"}
      ],
      "patterns": [
        {"type": "elaboration", "source_date": "2025-01-10"}
      ]
    }
  ]
}
```

---

## Content Generation Endpoints

### POST `/generate/course-script`

**Generate production-ready course script** from research.

**Request Body**:
```json
{
  "topic": "focus systems for knowledge workers",
  "audience": "creators, entrepreneurs",
  "format": "video_course",  // video_course, blog_post, email_sequence
  "length": {
    "modules": 6,
    "minutes_per_module": 20
  },
  "research_sources": {
    "authors": ["dankoe", "calnewport", "jamesclear"],
    "platforms": ["twitter", "youtube", "amazon"],
    "content_ids": ["uuid1", "uuid2"]  // Optional: specific sources
  },
  "style": "conversational",  // conversational, academic, direct
  "include_citations": true
}
```

**Response**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "estimated_time_seconds": 180
}
```

**Result (GET `/generate/jobs/{job_id}`):**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "script": {
    "title": "Building Unbreakable Focus Systems",
    "modules": [
      {
        "number": 1,
        "title": "The Focus Crisis",
        "duration_minutes": 20,
        "script": "## Hook (0:00-1:00)\n[SLIDE: Productivity stats]\n\n\"You're not lazy. You're drowning...\"\n\n## Problem (1:00-5:00)\n...",
        "slides": [
          {"timestamp": "0:00", "content": "Title slide", "notes": "Strong visual"},
          {"timestamp": "1:00", "content": "Stats graphic", "notes": "Source: Dan Koe tweet"}
        ],
        "citations": [
          {
            "text": "Average knowledge worker switches tasks every 3 minutes",
            "source": "Dan Koe tweet",
            "url": "https://twitter.com/dankoe/status/123"
          }
        ]
      }
    ],
    "total_words": 6847,
    "total_duration_minutes": 120,
    "readability_score": 7.2,  // Flesch-Kincaid grade level
    "source_count": 47
  },
  "metadata": {
    "generated_at": "2025-01-15T15:45:00Z",
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4.5",
    "tokens_used": 12456,
    "cost_usd": 0.187
  }
}
```

---

### POST `/generate/content-brief`

**Generate research-backed content brief**.

**Request Body**:
```json
{
  "topic": "productivity for ADHD creators",
  "format": "blog_post",  // blog_post, newsletter, tweet_thread
  "target_word_count": 2000,
  "include_sections": [
    "pain_points",
    "authority_quotes",
    "frameworks",
    "call_to_action"
  ]
}
```

**Response**: Similar structure to course script.

---

## Export Endpoints

### POST `/export/markdown`

**Export content as formatted markdown**.

**Request Body**:
```json
{
  "content_ids": ["uuid1", "uuid2"],
  "format": "markdown",
  "template": "research_report",  // research_report, newsletter, blog_post
  "options": {
    "include_citations": true,
    "include_metrics": true,
    "group_by": "platform"  // platform, author, date
  }
}
```

**Response**:
```json
{
  "export_id": "uuid",
  "file_url": "/exports/research_report_20250115.md",
  "preview": "# Research Report\n\n## Twitter Content\n\n### Dan Koe\n...",
  "word_count": 4567,
  "created_at": "2025-01-15T16:00:00Z"
}
```

---

### POST `/export/astro`

**Export to Astro static site**.

**Request Body**:
```json
{
  "content_ids": ["uuid"],
  "template": "newsletter_layout",
  "destination": "exports/astro-site/src/content/newsletters/",
  "build": true  // Trigger Astro build after export
}
```

**Response**:
```json
{
  "export_id": "uuid",
  "markdown_path": "exports/astro-site/src/content/newsletters/2025-01-15-focus-systems.md",
  "html_url": "http://localhost:3000/newsletters/focus-systems",
  "build_status": "success"
}
```

---

## Admin & Health Endpoints

### GET `/health`

**Health check**.

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "up",
    "redis": "up",
    "chromadb": "up",
    "scraping_workers": "up (4/4 active)"
  },
  "version": "1.0.0"
}
```

---

### GET `/stats`

**System statistics**.

**Response**:
```json
{
  "content": {
    "total": 145678,
    "by_platform": {
      "twitter": 89012,
      "youtube": 34567,
      "reddit": 15678,
      "amazon": 6421
    },
    "viral_content": 12456
  },
  "authors": {
    "total": 1234,
    "top_authorities": [
      {"name": "Dan Koe", "authority_score": 92.5},
      {"name": "Cal Newport", "authority_score": 88.3}
    ]
  },
  "usage": {
    "api_calls_today": 4567,
    "scraping_jobs_today": 234,
    "llm_tokens_used_today": 1234567,
    "cost_today_usd": 12.45
  }
}
```

---

### POST `/admin/reindex-vectors`

**Reindex all content embeddings** (admin only).

**Request Body**:
```json
{
  "platforms": ["twitter"],  // Optional: specific platforms
  "force": false  // Skip already-indexed content
}
```

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have exceeded your rate limit of 100 requests per hour",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2025-01-15T17:00:00Z"
    }
  }
}
```

**Error Codes**:
- `INVALID_REQUEST`: Malformed request
- `AUTHENTICATION_FAILED`: Invalid API key
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `RESOURCE_NOT_FOUND`: Content/job not found
- `SCRAPING_FAILED`: External scraping error
- `LLM_ERROR`: AI analysis failed
- `INTERNAL_ERROR`: Server error

---

## Rate Limits

| Tier | Requests/Hour | Scraping Jobs/Day | LLM Tokens/Day |
|------|---------------|-------------------|----------------|
| Free | 100 | 10 | 10,000 |
| Basic | 1,000 | 100 | 100,000 |
| Pro | 10,000 | 1,000 | 1,000,000 |

---

## Authentication

```bash
# Include API key in header
curl -H "X-API-Key: your_api_key_here" \
     https://api.unifiedscraper.com/scrape
```

---

**All endpoints ready for Day 2 implementation.**
