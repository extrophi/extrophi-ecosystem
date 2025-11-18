# Database Schema Design - IAC-032 Unified Scraper

**Stack**: PostgreSQL 16 + pgvector extension
**Purpose**: Unified multi-platform content storage with vector search

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Application Layer (FastAPI)                        │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  Database Layer (PostgreSQL + pgvector)             │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │   contents   │   authors    │  analyses    │    │
│  │  (unified)   │  (creators)  │  (LLM data)  │    │
│  └──────────────┴──────────────┴──────────────┘    │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │   patterns   │  frameworks  │   exports    │    │
│  │ (cross-plat) │  (AIDA/PAS)  │  (markdown)  │    │
│  └──────────────┴──────────────┴──────────────┘    │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  Vector Search (ChromaDB for dev, pgvector for prod)│
└─────────────────────────────────────────────────────┘
```

---

## Core Tables

### 1. contents (Unified Content Storage)

**Purpose**: Store ALL scraped content from ANY platform in unified schema.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE contents (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,  -- 'twitter', 'youtube', 'reddit', 'amazon', 'web'
    source_url TEXT UNIQUE NOT NULL,
    external_id VARCHAR(255),  -- Platform-specific ID (tweet ID, video ID, etc)

    -- Author
    author_id VARCHAR(255) NOT NULL,
    author_name VARCHAR(255),
    author_handle VARCHAR(255),

    -- Content
    content_type VARCHAR(50),  -- 'tweet', 'thread', 'video', 'post', 'review', 'article'
    title TEXT,
    body TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',

    -- Metadata
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Metrics (JSONB for flexibility)
    metrics JSONB DEFAULT '{}'::jsonb,
    -- Example: {"likes": 1234, "retweets": 567, "views": 89012, "engagement_rate": 0.045}

    -- Media
    media_urls TEXT[],
    thumbnail_url TEXT,

    -- Vector embedding (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding vector(1536),

    -- Analysis results (JSONB for flexibility)
    analysis JSONB DEFAULT '{}'::jsonb,
    -- Example: {"frameworks": ["AIDA"], "hooks": ["curiosity"], "sentiment": 0.8, "viral_score": 85}

    -- Platform-specific data that doesn't fit unified schema
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Flags
    is_viral BOOLEAN DEFAULT FALSE,
    is_analyzed BOOLEAN DEFAULT FALSE,
    is_indexed BOOLEAN DEFAULT FALSE,  -- Vector indexed in ChromaDB

    -- Constraints
    CONSTRAINT valid_platform CHECK (platform IN ('twitter', 'youtube', 'reddit', 'amazon', 'web', 'linkedin', 'tiktok'))
);

-- Indexes for performance
CREATE INDEX idx_contents_platform ON contents(platform);
CREATE INDEX idx_contents_author_id ON contents(author_id);
CREATE INDEX idx_contents_published_at ON contents(published_at DESC);
CREATE INDEX idx_contents_scraped_at ON contents(scraped_at DESC);
CREATE INDEX idx_contents_viral ON contents(is_viral) WHERE is_viral = TRUE;
CREATE INDEX idx_contents_metrics ON contents USING GIN (metrics);
CREATE INDEX idx_contents_analysis ON contents USING GIN (analysis);

-- Vector similarity search index (IVFFlat for speed, HNSW for accuracy)
CREATE INDEX idx_contents_embedding ON contents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search
CREATE INDEX idx_contents_body_fts ON contents USING GIN (to_tsvector('english', body));
CREATE INDEX idx_contents_title_fts ON contents USING GIN (to_tsvector('english', title));
```

**Sample Data**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "twitter",
  "source_url": "https://twitter.com/dankoe/status/1234567890",
  "external_id": "1234567890",
  "author_id": "dankoe",
  "author_name": "Dan Koe",
  "author_handle": "@dankoe",
  "content_type": "tweet",
  "title": null,
  "body": "Your focus determines your reality. Here's how to build unbreakable focus systems in 2025:",
  "language": "en",
  "published_at": "2025-01-15T14:30:00Z",
  "metrics": {
    "likes": 1234,
    "retweets": 567,
    "replies": 89,
    "views": 45678,
    "engagement_rate": 0.041
  },
  "media_urls": [],
  "embedding": [0.123, 0.456, ...],  // 1536 dimensions
  "analysis": {
    "frameworks": ["AIDA"],
    "hooks": ["curiosity", "number"],
    "sentiment": 0.85,
    "viral_score": 92,
    "themes": ["productivity", "focus"]
  },
  "is_viral": true,
  "is_analyzed": true
}
```

---

### 2. authors (Creator Profiles)

**Purpose**: Track creators across platforms, calculate authority scores.

```sql
CREATE TABLE authors (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    handle VARCHAR(255),
    name VARCHAR(255),

    -- Profile
    bio TEXT,
    location VARCHAR(255),
    website_url TEXT,
    profile_image_url TEXT,
    verified BOOLEAN DEFAULT FALSE,

    -- Metrics
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    content_count INTEGER DEFAULT 0,

    -- Calculated metrics
    avg_engagement_rate FLOAT,
    authority_score FLOAT,  -- Calculated: (followers * avg_engagement * content_quality) / 1000

    -- Timestamps
    account_created_at TIMESTAMP,
    first_scraped_at TIMESTAMP DEFAULT NOW(),
    last_scraped_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE(platform, external_id)
);

CREATE INDEX idx_authors_platform ON authors(platform);
CREATE INDEX idx_authors_handle ON authors(handle);
CREATE INDEX idx_authors_authority_score ON authors(authority_score DESC NULLS LAST);
CREATE INDEX idx_authors_followers ON authors(followers_count DESC);
```

**Authority Score Calculation**:
```sql
CREATE OR REPLACE FUNCTION calculate_authority_score(author_uuid UUID)
RETURNS FLOAT AS $$
DECLARE
    follower_score FLOAT;
    engagement_score FLOAT;
    content_quality FLOAT;
BEGIN
    -- Get author metrics
    SELECT
        LEAST(followers_count / 1000.0, 100),  -- Cap at 100K followers
        COALESCE(avg_engagement_rate * 100, 0),
        (SELECT AVG((metrics->>'engagement_rate')::float)
         FROM contents
         WHERE author_id = (SELECT external_id FROM authors WHERE id = author_uuid)
         AND is_viral = TRUE) * 100
    INTO follower_score, engagement_score, content_quality
    FROM authors
    WHERE id = author_uuid;

    -- Weighted formula: 30% followers, 40% engagement, 30% content quality
    RETURN (follower_score * 0.3) + (engagement_score * 0.4) + (COALESCE(content_quality, 0) * 0.3);
END;
$$ LANGUAGE plpgsql;
```

---

### 3. analyses (LLM Analysis Results)

**Purpose**: Store detailed LLM analysis separately from content for versioning.

```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES contents(id) ON DELETE CASCADE,

    -- Analysis metadata
    analysis_type VARCHAR(100) NOT NULL,  -- 'framework', 'hooks', 'sentiment', 'themes', 'viral_prediction'
    llm_provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'google'
    llm_model VARCHAR(100) NOT NULL,  -- 'gpt-4o', 'claude-sonnet-4.5', etc
    prompt_version VARCHAR(50),

    -- Results
    result JSONB NOT NULL,
    confidence_score FLOAT,  -- 0.0-1.0

    -- Performance tracking
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    cost_usd NUMERIC(10, 6),

    -- Timestamps
    analyzed_at TIMESTAMP DEFAULT NOW(),

    -- Versioning
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_analyses_content_id ON analyses(content_id);
CREATE INDEX idx_analyses_type ON analyses(analysis_type);
CREATE INDEX idx_analyses_provider ON analyses(llm_provider);
CREATE INDEX idx_analyses_analyzed_at ON analyses(analyzed_at DESC);
```

**Sample Analysis**:
```json
{
  "content_id": "550e8400-...",
  "analysis_type": "framework_detection",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "result": {
    "frameworks_detected": ["AIDA"],
    "breakdown": {
      "attention": "Your focus determines your reality",
      "interest": "Here's how to build",
      "desire": "unbreakable focus systems",
      "action": "in 2025" (implied CTA in thread)
    },
    "confidence": 0.92
  },
  "confidence_score": 0.92,
  "tokens_used": 234,
  "processing_time_ms": 1456,
  "cost_usd": 0.000587
}
```

---

### 4. patterns (Cross-Platform Content Patterns)

**Purpose**: Track content repurposing patterns (Dan Koe's tweet→newsletter→video strategy).

```sql
CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    author_id UUID REFERENCES authors(id),

    -- Pattern metadata
    pattern_type VARCHAR(100) NOT NULL,  -- 'elaboration', 'repurposing', 'thread_to_video', 'test_and_expand'
    description TEXT,

    -- Content relationships
    source_content_id UUID REFERENCES contents(id),
    related_content_ids UUID[],  -- Array of related content IDs

    -- Similarity metrics
    semantic_similarity FLOAT,  -- Cosine similarity of embeddings
    temporal_gap_days INTEGER,  -- Days between source and related content

    -- Insights
    insights JSONB DEFAULT '{}'::jsonb,
    -- Example: {"expansion_ratio": 3.5, "platforms": ["twitter", "youtube"], "engagement_lift": 2.3}

    confidence_score FLOAT,
    detected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_patterns_author_id ON patterns(author_id);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_source_content ON patterns(source_content_id);
CREATE INDEX idx_patterns_similarity ON patterns(semantic_similarity DESC);
```

**Pattern Detection Query**:
```sql
-- Find elaboration patterns (tweet expanded to YouTube video)
SELECT
    c1.id as source_id,
    c1.platform as source_platform,
    c1.body as source_text,
    c2.id as related_id,
    c2.platform as related_platform,
    c2.title as related_title,
    1 - (c1.embedding <=> c2.embedding) as similarity,
    EXTRACT(DAY FROM (c2.published_at - c1.published_at)) as days_between
FROM contents c1
JOIN contents c2 ON c1.author_id = c2.author_id
WHERE c1.platform = 'twitter'
  AND c2.platform = 'youtube'
  AND c1.published_at < c2.published_at
  AND 1 - (c1.embedding <=> c2.embedding) > 0.85  -- High semantic similarity
  AND EXTRACT(DAY FROM (c2.published_at - c1.published_at)) BETWEEN 1 AND 30
ORDER BY similarity DESC
LIMIT 100;
```

---

### 5. frameworks (Copywriting Framework Library)

**Purpose**: Store identified copywriting frameworks for training and reference.

```sql
CREATE TABLE frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,  -- 'AIDA', 'PAS', 'BAB', 'PASTOR', 'FAB', '4Ps'
    full_name TEXT,  -- 'Attention Interest Desire Action'

    -- Structure
    components TEXT[],  -- ['Attention', 'Interest', 'Desire', 'Action']
    description TEXT,

    -- Examples
    example_content_ids UUID[],  -- Links to contents table

    -- Usage stats
    usage_count INTEGER DEFAULT 0,
    avg_engagement_rate FLOAT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_frameworks_name ON frameworks(name);

-- Seed data
INSERT INTO frameworks (name, full_name, components, description) VALUES
('AIDA', 'Attention Interest Desire Action',
 ARRAY['Attention', 'Interest', 'Desire', 'Action'],
 'Classic advertising formula: grab attention, build interest, create desire, prompt action'),
('PAS', 'Problem Agitate Solution',
 ARRAY['Problem', 'Agitate', 'Solution'],
 'Identify pain point, amplify consequences, present solution'),
('BAB', 'Before After Bridge',
 ARRAY['Before', 'After', 'Bridge'],
 'Current situation, improved outcome, how to get there'),
('PASTOR', 'Problem Amplify Story Transformation Offer Response',
 ARRAY['Problem', 'Amplify', 'Story', 'Transformation', 'Offer', 'Response'],
 'Comprehensive framework for long-form sales copy');
```

---

### 6. exports (Generated Content Tracking)

**Purpose**: Track generated course scripts, markdown exports, content briefs.

```sql
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Export metadata
    export_type VARCHAR(100) NOT NULL,  -- 'course_script', 'markdown_report', 'tweet_thread', 'blog_outline'
    title VARCHAR(500),
    format VARCHAR(50),  -- 'markdown', 'html', 'json', 'pdf'

    -- Source content
    source_content_ids UUID[],  -- Which contents were synthesized
    query_prompt TEXT,  -- User's original query

    -- Generated content
    content TEXT NOT NULL,
    word_count INTEGER,

    -- Quality metrics
    readability_score FLOAT,  -- Flesch-Kincaid grade level
    citation_count INTEGER,  -- Number of sources cited

    -- Metadata
    generated_at TIMESTAMP DEFAULT NOW(),
    generated_by VARCHAR(100),  -- 'gpt-4o', 'claude-sonnet-4.5', 'user'

    -- Export tracking
    exported_to TEXT[],  -- ['astro_site', 'notion', 'email']
    export_urls JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_exports_type ON exports(export_type);
CREATE INDEX idx_exports_generated_at ON exports(generated_at DESC);
```

---

## Helper Views

### Top Viral Content by Platform

```sql
CREATE VIEW top_viral_content AS
SELECT
    platform,
    author_name,
    body,
    (metrics->>'likes')::int as likes,
    (metrics->>'engagement_rate')::float as engagement_rate,
    published_at
FROM contents
WHERE is_viral = TRUE
ORDER BY (metrics->>'engagement_rate')::float DESC;
```

### Author Authority Rankings

```sql
CREATE VIEW author_rankings AS
SELECT
    a.name,
    a.handle,
    a.platform,
    a.followers_count,
    a.avg_engagement_rate,
    calculate_authority_score(a.id) as authority_score,
    COUNT(c.id) as content_count,
    COUNT(c.id) FILTER (WHERE c.is_viral) as viral_content_count
FROM authors a
LEFT JOIN contents c ON a.external_id = c.author_id AND a.platform = c.platform
GROUP BY a.id, a.name, a.handle, a.platform, a.followers_count, a.avg_engagement_rate
ORDER BY authority_score DESC;
```

---

## Migration Strategy

### From IAC-024 (SQLite) to Production (PostgreSQL)

```sql
-- Migrate tweets table → contents table
INSERT INTO contents (
    platform,
    source_url,
    external_id,
    author_id,
    author_name,
    content_type,
    body,
    published_at,
    metrics,
    is_viral
)
SELECT
    'twitter' as platform,
    'https://twitter.com/' || username || '/status/' || id as source_url,
    id as external_id,
    user_id as author_id,
    username as author_name,
    'tweet' as content_type,
    content as body,
    created_at as published_at,
    jsonb_build_object(
        'likes', likes,
        'retweets', retweets,
        'replies', replies
    ) as metrics,
    (viral_score > 80) as is_viral
FROM legacy_tweets;  -- IAC-024 tweets table
```

---

## Performance Tuning

### Vacuum and Analyze Schedule

```sql
-- Weekly VACUUM for contents table (high write volume)
SELECT cron.schedule('vacuum-contents', '0 3 * * 0', 'VACUUM ANALYZE contents');

-- Daily ANALYZE for query planning
SELECT cron.schedule('analyze-all', '0 2 * * *', 'ANALYZE');
```

### Partitioning Strategy (Future Scale)

```sql
-- Partition contents by platform + month for massive scale
CREATE TABLE contents_twitter_2025_01 PARTITION OF contents
FOR VALUES IN ('twitter')
WHERE published_at >= '2025-01-01' AND published_at < '2025-02-01';
```

---

## Backup and Recovery

```bash
# Daily backups
pg_dump -Fc unified_scraper > backup_$(date +%Y%m%d).dump

# Point-in-time recovery
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

---

## Security

```sql
-- Read-only user for analytics
CREATE ROLE analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- Application user with limited permissions
CREATE ROLE app_user;
GRANT SELECT, INSERT, UPDATE ON contents, authors, analyses, patterns TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

---

**Next Steps:**
1. Deploy schema to local PostgreSQL
2. Create migration scripts from IAC-024 SQLite
3. Load sample data (100 Dan Koe tweets)
4. Test vector similarity queries
5. Benchmark performance with 100K+ rows

**This schema is ready for Day 2 implementation.**
