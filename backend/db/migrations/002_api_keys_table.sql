-- Migration: 002 - API Keys Table
-- Description: Add API keys table for authentication and rate limiting
-- Date: 2025-11-18
-- Author: RHO Agent
-- Dependencies: 001_backend_module_schema.sql (users table must exist)

-- ============================================================================
-- API KEYS TABLE
-- Table for managing multiple API keys per user with rate limiting
-- ============================================================================

-- API Keys table: Secure API key authentication with rate limiting
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Key identification
    key_name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL, -- First 8 chars for identification (e.g., "sk_live_")
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- SHA-256 hash of the full key

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,

    -- Rate limiting (1000 requests per hour)
    rate_limit_requests INTEGER NOT NULL DEFAULT 1000,
    rate_limit_window_seconds INTEGER NOT NULL DEFAULT 3600, -- 1 hour
    current_usage_count INTEGER NOT NULL DEFAULT 0,
    rate_limit_window_start TIMESTAMP,

    -- Usage tracking
    last_used_at TIMESTAMP,
    request_count BIGINT NOT NULL DEFAULT 0, -- Total requests made with this key

    -- Expiration
    expires_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,

    -- Constraints
    CONSTRAINT api_key_name_unique_per_user UNIQUE (user_id, key_name)
);

-- Create indices for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_revoked ON api_keys(is_revoked);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_active ON api_keys(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_last_used_at ON api_keys(last_used_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at);

-- ============================================================================
-- TRIGGERS FOR API KEYS
-- ============================================================================

-- Trigger to update updated_at on api_keys table
DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to set revoked_at when is_revoked changes to true
CREATE OR REPLACE FUNCTION set_api_key_revoked_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_revoked = TRUE AND OLD.is_revoked = FALSE THEN
        NEW.revoked_at = CURRENT_TIMESTAMP;
        NEW.is_active = FALSE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_revoked_at_on_api_keys ON api_keys;
CREATE TRIGGER set_revoked_at_on_api_keys BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION set_api_key_revoked_at();

-- ============================================================================
-- COMMENTS FOR API KEYS TABLE
-- ============================================================================

COMMENT ON TABLE api_keys IS 'API keys for authentication with rate limiting (1000 req/hour per key)';
COMMENT ON COLUMN api_keys.key_name IS 'User-friendly name for the API key (e.g., "Production API", "Development")';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8-12 characters of the key for identification (e.g., "sk_live_ab")';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the full API key (never store plaintext)';
COMMENT ON COLUMN api_keys.is_active IS 'Whether the key is currently active and can be used';
COMMENT ON COLUMN api_keys.is_revoked IS 'Whether the key has been permanently revoked';
COMMENT ON COLUMN api_keys.rate_limit_requests IS 'Maximum number of requests allowed per window (default: 1000)';
COMMENT ON COLUMN api_keys.rate_limit_window_seconds IS 'Rate limit window in seconds (default: 3600 = 1 hour)';
COMMENT ON COLUMN api_keys.current_usage_count IS 'Current number of requests in the current window';
COMMENT ON COLUMN api_keys.rate_limit_window_start IS 'Start time of the current rate limit window';
COMMENT ON COLUMN api_keys.last_used_at IS 'Timestamp of the last API request using this key';
COMMENT ON COLUMN api_keys.request_count IS 'Total number of requests made with this key (all time)';
COMMENT ON COLUMN api_keys.expires_at IS 'Optional expiration timestamp for the key';
