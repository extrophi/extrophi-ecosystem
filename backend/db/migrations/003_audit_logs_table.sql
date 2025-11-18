-- Migration: 003 - Audit Logs Table
-- Description: Add audit logs table for tracking all API requests/responses
-- Date: 2025-11-18
-- Author: BETA-2 Agent
-- Dependencies: 001_backend_module_schema.sql, 002_api_keys_table.sql

-- ============================================================================
-- AUDIT LOGS TABLE
-- Table for logging all API requests and responses for security and compliance
-- ============================================================================

-- Audit logs table: Track all API calls with request/response details
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Request identification
    endpoint VARCHAR(500) NOT NULL,  -- /api/scrape, /api/query, etc.
    method VARCHAR(10) NOT NULL,     -- GET, POST, PUT, DELETE, etc.
    path TEXT NOT NULL,              -- Full path with query params

    -- User/API key tracking
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    api_key_prefix VARCHAR(20),      -- For quick identification

    -- Request details
    request_headers JSONB DEFAULT '{}',   -- Headers (sensitive ones filtered)
    request_params JSONB DEFAULT '{}',    -- Query params
    request_body JSONB DEFAULT '{}',      -- Request body (if JSON)

    -- Response details
    response_status INTEGER NOT NULL,     -- 200, 404, 500, etc.
    response_body JSONB DEFAULT '{}',     -- Response body (if JSON, truncated if large)
    response_size_bytes BIGINT,           -- Response size in bytes

    -- Performance metrics
    duration_ms INTEGER NOT NULL,         -- Request duration in milliseconds

    -- Client information
    client_ip VARCHAR(45),                -- IPv4 or IPv6
    user_agent TEXT,                      -- User-Agent header

    -- Metadata
    error_message TEXT,                   -- Error message if request failed
    metadata JSONB DEFAULT '{}',          -- Additional context

    -- Timestamp (immutable - no updates)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for audit_logs (optimized for common queries)
CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint ON audit_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_audit_logs_method ON audit_logs(method);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_api_key_id ON audit_logs(api_key_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_response_status ON audit_logs(response_status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_client_ip ON audit_logs(client_ip);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Composite indices for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint_created ON audit_logs(endpoint, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_status_created ON audit_logs(response_status, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint_status ON audit_logs(endpoint, response_status);

-- ============================================================================
-- COMMENTS FOR AUDIT LOGS TABLE
-- ============================================================================

COMMENT ON TABLE audit_logs IS 'Audit trail of all API requests and responses for security, compliance, and debugging';
COMMENT ON COLUMN audit_logs.endpoint IS 'API endpoint path (e.g., /api/scrape, /api/query)';
COMMENT ON COLUMN audit_logs.method IS 'HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)';
COMMENT ON COLUMN audit_logs.path IS 'Full request path including query parameters';
COMMENT ON COLUMN audit_logs.user_id IS 'User ID if request was authenticated (NULL for unauthenticated requests)';
COMMENT ON COLUMN audit_logs.api_key_id IS 'API key ID if request used API key authentication';
COMMENT ON COLUMN audit_logs.api_key_prefix IS 'First 15 chars of API key for identification without exposing full key';
COMMENT ON COLUMN audit_logs.request_headers IS 'Request headers (sensitive headers like Authorization are filtered)';
COMMENT ON COLUMN audit_logs.request_params IS 'Query parameters from the request URL';
COMMENT ON COLUMN audit_logs.request_body IS 'Request body if JSON (sensitive fields like password are redacted)';
COMMENT ON COLUMN audit_logs.response_status IS 'HTTP response status code (200, 404, 500, etc.)';
COMMENT ON COLUMN audit_logs.response_body IS 'Response body if JSON and < 10KB (larger responses not stored)';
COMMENT ON COLUMN audit_logs.response_size_bytes IS 'Size of response body in bytes';
COMMENT ON COLUMN audit_logs.duration_ms IS 'Request processing duration in milliseconds';
COMMENT ON COLUMN audit_logs.client_ip IS 'Client IP address (supports both IPv4 and IPv6)';
COMMENT ON COLUMN audit_logs.user_agent IS 'User-Agent header from the request';
COMMENT ON COLUMN audit_logs.error_message IS 'Error message if request failed or threw an exception';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional context and metadata for the request';
COMMENT ON COLUMN audit_logs.created_at IS 'Timestamp when the request was logged (immutable)';

-- ============================================================================
-- DATA RETENTION POLICY (Optional)
-- ============================================================================

-- Create a function to automatically delete audit logs older than 90 days
-- This can be called via a cron job or scheduled task
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_audit_logs IS 'Delete audit logs older than specified days (default: 90). Returns number of deleted rows.';
