-- Research Module Database Schema
-- PostgreSQL with pgvector extension for semantic search and content enrichment

-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE CONTENT TABLES
-- ============================================================================

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
    authority_score DECIMAL(3,2),
    profile_url TEXT,
    avatar_url TEXT,
    metadata JSONB DEFAULT '{}',
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT authors_platform_username_unique UNIQUE (platform, username)
);

-- Create indices for authors
CREATE INDEX IF NOT EXISTS idx_authors_platform ON authors(platform);
CREATE INDEX IF NOT EXISTS idx_authors_username ON authors(username);
CREATE INDEX IF NOT EXISTS idx_authors_platform_username ON authors(platform, username);
CREATE INDEX IF NOT EXISTS idx_authors_authority_score ON authors(authority_score DESC);
CREATE INDEX IF NOT EXISTS idx_authors_discovered_at ON authors(discovered_at DESC);

-- Contents table: Unified storage for scraped content across all platforms
CREATE TABLE IF NOT EXISTS contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
CREATE INDEX IF NOT EXISTS idx_contents_platform_published_at ON contents(platform, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_contents_scraped_at ON contents(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_contents_analyzed_at ON contents(analyzed_at DESC) WHERE analyzed_at IS NOT NULL;

-- IVFFlat index for efficient cosine similarity search on embeddings
CREATE INDEX IF NOT EXISTS idx_contents_embedding_cosine
    ON contents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Comments for documentation
COMMENT ON TABLE authors IS 'Content creators/authors across all platforms (Twitter, YouTube, Reddit, etc.)';
COMMENT ON TABLE contents IS 'Unified content storage with embeddings for semantic search and cross-platform analysis';
COMMENT ON COLUMN contents.embedding IS 'OpenAI ada-002 embedding (1536 dimensions) for semantic search via pgvector';
