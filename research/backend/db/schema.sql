-- ============================================================================
-- Research Module Database Schema
-- PostgreSQL + pgvector for semantic content search
-- ============================================================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Drop existing tables (for fresh setup)
-- ============================================================================

DROP TABLE IF EXISTS scrape_jobs CASCADE;
DROP TABLE IF EXISTS contents CASCADE;
DROP TABLE IF EXISTS sources CASCADE;

-- ============================================================================
-- Core Tables
-- ============================================================================

-- Sources: Platform-specific content sources
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,  -- twitter, youtube, reddit, web
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,  -- Platform-specific metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contents: Scraped content with vector embeddings
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,  -- text, transcript, post, comment
    text_content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 embeddings (1536 dimensions)
    word_count INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    metadata JSONB DEFAULT '{}'::jsonb,  -- Content-specific metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scrape Jobs: Async job tracking
CREATE TABLE scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    platform VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    depth INTEGER DEFAULT 1,
    extract_embeddings BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_seconds REAL,
    items_scraped INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Source indexes
CREATE INDEX idx_sources_platform ON sources(platform);
CREATE INDEX idx_sources_published_at ON sources(published_at DESC);
CREATE INDEX idx_sources_scraped_at ON sources(scraped_at DESC);
CREATE INDEX idx_sources_metadata ON sources USING gin(metadata);

-- Content indexes
CREATE INDEX idx_contents_source_id ON contents(source_id);
CREATE INDEX idx_contents_content_type ON contents(content_type);
CREATE INDEX idx_contents_created_at ON contents(created_at DESC);
CREATE INDEX idx_contents_word_count ON contents(word_count);
CREATE INDEX idx_contents_metadata ON contents USING gin(metadata);

-- Vector similarity search index (IVFFlat for fast approximate search)
-- List size formula: rows / 1000 for < 1M rows
CREATE INDEX idx_contents_embedding ON contents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Job indexes
CREATE INDEX idx_jobs_status ON scrape_jobs(status);
CREATE INDEX idx_jobs_created_at ON scrape_jobs(created_at DESC);
CREATE INDEX idx_jobs_platform ON scrape_jobs(platform);

-- ============================================================================
-- Functions for Vector Similarity Search
-- ============================================================================

-- Function: Find similar content using cosine similarity
-- Returns content most similar to the query embedding
CREATE OR REPLACE FUNCTION find_similar_content(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    content_id UUID,
    source_id UUID,
    text_content TEXT,
    similarity_score FLOAT,
    platform VARCHAR(50),
    url TEXT,
    title TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS content_id,
        c.source_id,
        c.text_content,
        1 - (c.embedding <=> query_embedding) AS similarity_score,
        s.platform,
        s.url,
        s.title,
        s.author,
        s.published_at
    FROM contents c
    JOIN sources s ON c.source_id = s.id
    WHERE c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Find similar content by platform
CREATE OR REPLACE FUNCTION find_similar_content_by_platform(
    query_embedding vector(1536),
    target_platform VARCHAR(50),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    content_id UUID,
    source_id UUID,
    text_content TEXT,
    similarity_score FLOAT,
    url TEXT,
    title TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS content_id,
        c.source_id,
        c.text_content,
        1 - (c.embedding <=> query_embedding) AS similarity_score,
        s.url,
        s.title,
        s.author,
        s.published_at
    FROM contents c
    JOIN sources s ON c.source_id = s.id
    WHERE c.embedding IS NOT NULL
        AND s.platform = target_platform
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Get content statistics
CREATE OR REPLACE FUNCTION get_content_statistics()
RETURNS TABLE (
    platform VARCHAR(50),
    content_count BIGINT,
    avg_word_count FLOAT,
    total_sources BIGINT,
    latest_scrape TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.platform,
        COUNT(c.id) AS content_count,
        AVG(c.word_count)::FLOAT AS avg_word_count,
        COUNT(DISTINCT s.id) AS total_sources,
        MAX(s.scraped_at) AS latest_scrape
    FROM sources s
    LEFT JOIN contents c ON s.id = c.source_id
    GROUP BY s.platform
    ORDER BY content_count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers for Updated Timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contents_updated_at
    BEFORE UPDATE ON contents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scrape_jobs_updated_at
    BEFORE UPDATE ON scrape_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Insert sample source
INSERT INTO sources (platform, url, title, author, published_at) VALUES
('web', 'https://example.com/article', 'Sample Article', 'John Doe', CURRENT_TIMESTAMP);

-- Insert sample content (without embedding for now - will be added by LAMBDA agent)
INSERT INTO contents (source_id, content_type, text_content, word_count)
SELECT id, 'text', 'This is sample content for testing the database schema.', 9
FROM sources WHERE url = 'https://example.com/article';

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify pgvector extension
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Verify tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Verify indexes
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;

-- Count records
SELECT 'sources' as table_name, COUNT(*) as count FROM sources
UNION ALL
SELECT 'contents', COUNT(*) FROM contents
UNION ALL
SELECT 'scrape_jobs', COUNT(*) FROM scrape_jobs;
