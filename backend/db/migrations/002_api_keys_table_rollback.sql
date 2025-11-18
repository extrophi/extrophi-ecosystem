-- Rollback Migration: 002 - API Keys Table
-- Description: Remove API keys table
-- Date: 2025-11-18

-- Drop triggers first
DROP TRIGGER IF EXISTS set_revoked_at_on_api_keys ON api_keys;
DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;

-- Drop functions
DROP FUNCTION IF EXISTS set_api_key_revoked_at();

-- Drop table
DROP TABLE IF EXISTS api_keys CASCADE;
