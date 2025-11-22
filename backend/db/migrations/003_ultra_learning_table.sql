-- Migration: Add ultra_learning table
-- Date: 2025-11-22
-- Description: Create table for storing ultra learning formatted content

-- Ultra Learning table: Structured learning content extracted from scraped content
CREATE TABLE IF NOT EXISTS ultra_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL UNIQUE REFERENCES contents(id) ON DELETE CASCADE,

    -- Original content metadata
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    author_id VARCHAR(255) NOT NULL,

    -- Ultra Learning structured data
    meta_subject TEXT NOT NULL,
    concepts TEXT[] DEFAULT '{}',
    facts TEXT[] DEFAULT '{}',
    procedures TEXT[] DEFAULT '{}',

    -- Processing metadata
    llm_model VARCHAR(100) DEFAULT 'claude-haiku-4-20250514',
    tokens_used INTEGER,
    cost_cents INTEGER,
    processing_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for ultra_learning table
CREATE INDEX IF NOT EXISTS idx_ultra_learning_content_id ON ultra_learning(content_id);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_meta_subject ON ultra_learning(meta_subject);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_platform ON ultra_learning(platform);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_author_id ON ultra_learning(author_id);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_created_at ON ultra_learning(created_at);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_concepts ON ultra_learning USING GIN (concepts);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_facts ON ultra_learning USING GIN (facts);
CREATE INDEX IF NOT EXISTS idx_ultra_learning_procedures ON ultra_learning USING GIN (procedures);

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_ultra_learning_updated_at ON ultra_learning;
CREATE TRIGGER update_ultra_learning_updated_at BEFORE UPDATE ON ultra_learning
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE ultra_learning IS 'Ultra learning formatted content extracted from scraped content using Claude Haiku';
COMMENT ON COLUMN ultra_learning.content_id IS 'Foreign key to contents table (one-to-one relationship)';
COMMENT ON COLUMN ultra_learning.meta_subject IS 'Main topic/subject of the content';
COMMENT ON COLUMN ultra_learning.concepts IS 'Key ideas, frameworks, and concepts';
COMMENT ON COLUMN ultra_learning.facts IS 'Statistics, data points, and factual information';
COMMENT ON COLUMN ultra_learning.procedures IS 'Step-by-step instructions and processes';
COMMENT ON COLUMN ultra_learning.llm_model IS 'LLM model used for extraction (default: claude-haiku-4-20250514)';
COMMENT ON COLUMN ultra_learning.tokens_used IS 'Number of tokens used for processing';
COMMENT ON COLUMN ultra_learning.cost_cents IS 'Cost in cents for LLM processing';
