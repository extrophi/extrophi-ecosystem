-- Rollback Migration 001: Remove Cards and $EXTROPY System
-- Created: 2025-11-18
-- Description: Safely removes all tables, functions, triggers, and views added in migration 001

-- Drop views first (depend on tables)
DROP VIEW IF EXISTS card_details;
DROP VIEW IF EXISTS user_stats;

-- Drop functions
DROP FUNCTION IF EXISTS process_attribution_payment(UUID);
DROP FUNCTION IF EXISTS award_publish_extropy(UUID, UUID, DECIMAL);
DROP FUNCTION IF EXISTS transfer_extropy(UUID, UUID, DECIMAL, UUID, TEXT);
DROP FUNCTION IF EXISTS set_published_at();
DROP FUNCTION IF EXISTS update_user_extropy_stats();
DROP FUNCTION IF EXISTS update_user_card_count();
DROP FUNCTION IF EXISTS prevent_negative_extropy_balance();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS sync_state CASCADE;
DROP TABLE IF EXISTS extropy_ledger CASCADE;
DROP TABLE IF EXISTS attributions CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Note: We don't drop the uuid-ossp extension as it may be used by other parts of the system
-- If you need to drop it: DROP EXTENSION IF EXISTS "uuid-ossp";
