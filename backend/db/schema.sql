-- IAC-032 Unified Scraper Database Schema
-- PostgreSQL with pgvector extension for semantic search

-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Authors table: Store creator/author information across platforms
CREATE TABLE IF NOT EXISTS authors (
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(500),
    bio TEXT,
    follower_count VARCHAR(20),
    following_count VARCHAR(20),
    content_count VARCHAR(20),
    authority_score VARCHAR(10),
    profile_url TEXT,
    avatar_url TEXT,
    metadata JSONB DEFAULT '{}',
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT authors_platform_username_unique UNIQUE (platform, username)
);

-- Create indices for authors
CREATE INDEX IF NOT EXISTS idx_authors_platform_username ON authors(platform, username);
CREATE INDEX IF NOT EXISTS idx_authors_authority_score ON authors(authority_score);
CREATE INDEX IF NOT EXISTS idx_authors_discovered_at ON authors(discovered_at);

-- Contents table: Unified storage for content across all platforms
CREATE TABLE IF NOT EXISTS contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    author_id VARCHAR(255) NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    content_title TEXT,
    content_body TEXT NOT NULL,
    published_at TIMESTAMP,
    metrics JSONB DEFAULT '{}',
    analysis JSONB DEFAULT '{}',
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for contents table
CREATE INDEX IF NOT EXISTS idx_contents_platform ON contents(platform);
CREATE INDEX IF NOT EXISTS idx_contents_author_id ON contents(author_id);
CREATE INDEX IF NOT EXISTS idx_contents_source_url ON contents(source_url);
CREATE INDEX IF NOT EXISTS idx_contents_platform_author_id ON contents(platform, author_id);
CREATE INDEX IF NOT EXISTS idx_contents_platform_published_at ON contents(platform, published_at);
CREATE INDEX IF NOT EXISTS idx_contents_scraped_at ON contents(scraped_at);
CREATE INDEX IF NOT EXISTS idx_contents_analyzed_at ON contents(analyzed_at);

-- IVFFlat index for efficient cosine similarity search on embeddings
-- This enables fast semantic search queries with pgvector
CREATE INDEX IF NOT EXISTS idx_contents_embedding_ivfflat
    ON contents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Patterns table: Cross-platform pattern detection
CREATE TABLE IF NOT EXISTS patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id VARCHAR(255) NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    content_ids JSONB NOT NULL DEFAULT '[]',
    confidence_score VARCHAR(10),
    analysis JSONB DEFAULT '{}',
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for patterns
CREATE INDEX IF NOT EXISTS idx_patterns_author_id ON patterns(author_id);
CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type ON patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_author_pattern_type ON patterns(author_id, pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_discovered_at ON patterns(discovered_at);

-- Research sessions table: Track research queries and generated outputs
CREATE TABLE IF NOT EXISTS research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(255) NOT NULL,
    project_brief TEXT,
    target_authorities JSONB DEFAULT '[]',
    platforms JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    total_pieces_scraped VARCHAR(20) DEFAULT '0',
    total_pieces_analyzed VARCHAR(20) DEFAULT '0',
    patterns_detected VARCHAR(20) DEFAULT '0',
    outputs JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'in_progress',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indices for research sessions
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_research_sessions_session_name ON research_sessions(session_name);

-- Content analysis details table: Store detailed analysis per piece
CREATE TABLE IF NOT EXISTS content_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL UNIQUE REFERENCES contents(id) ON DELETE CASCADE,
    frameworks TEXT[] DEFAULT '{}',
    hooks TEXT[] DEFAULT '{}',
    themes TEXT[] DEFAULT '{}',
    pain_points TEXT[] DEFAULT '{}',
    desires TEXT[] DEFAULT '{}',
    key_insights TEXT[] DEFAULT '{}',
    sentiment VARCHAR(50),
    tone VARCHAR(50),
    target_audience TEXT,
    call_to_action TEXT,
    raw_analysis JSONB,
    llm_model VARCHAR(100),
    tokens_used INTEGER,
    cost_cents INTEGER,
    analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for content analysis
CREATE INDEX IF NOT EXISTS idx_content_analysis_content_id ON content_analysis(content_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_sentiment ON content_analysis(sentiment);
CREATE INDEX IF NOT EXISTS idx_content_analysis_analyzed_at ON content_analysis(analyzed_at);

-- Scrape jobs tracking table: Monitor scraping status and results
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    query_params JSONB DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for scrape jobs
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_platform ON scrape_jobs(platform);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_created_at ON scrape_jobs(created_at);

-- Create or update function for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_authors_updated_at ON authors;
CREATE TRIGGER update_authors_updated_at BEFORE UPDATE ON authors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_contents_updated_at ON contents;
CREATE TRIGGER update_contents_updated_at BEFORE UPDATE ON contents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE authors IS 'Stores creator/author information across all platforms (Twitter, YouTube, Reddit, etc.)';
COMMENT ON TABLE contents IS 'Unified content storage with embeddings for semantic search and cross-platform analysis';
COMMENT ON TABLE patterns IS 'Detected cross-platform patterns (elaboration, themes, hooks, frameworks)';
COMMENT ON TABLE research_sessions IS 'Tracks research sessions, queries, and generated outputs (course scripts, briefs)';
COMMENT ON TABLE content_analysis IS 'Detailed LLM analysis results for each piece of content';
COMMENT ON TABLE scrape_jobs IS 'Monitoring and tracking of scraping jobs across platforms';

COMMENT ON COLUMN contents.embedding IS 'OpenAI embedding (1536 dimensions) for semantic search via pgvector';
COMMENT ON COLUMN contents.metrics IS 'Platform-specific metrics: likes, views, retweets, engagement_rate, etc.';
COMMENT ON COLUMN contents.analysis IS 'LLM analysis results: frameworks, hooks, themes, insights';
COMMENT ON COLUMN patterns.content_ids IS 'Array of content UUIDs that form this pattern';
COMMENT ON COLUMN research_sessions.outputs IS 'Generated outputs: {course_script: ..., briefs: ..., etc.}';
