-- Rollback Migration: 001 - Backend Module Schema
-- Description: Drop all Backend module tables (users, cards, attributions, extropy_ledger, sync_state)
-- Date: 2025-11-18
-- Author: OMICRON Agent
-- WARNING: This will delete all data in these tables!

-- ============================================================================
-- DROP BACKEND MODULE TABLES IN REVERSE DEPENDENCY ORDER
-- ============================================================================

-- Drop triggers first
DROP TRIGGER IF EXISTS prevent_negative_balance ON users;
DROP TRIGGER IF EXISTS prevent_extropy_ledger_update ON extropy_ledger;
DROP TRIGGER IF EXISTS prevent_extropy_ledger_delete ON extropy_ledger;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_cards_updated_at ON cards;
DROP TRIGGER IF EXISTS update_sync_state_updated_at ON sync_state;

-- Drop functions
DROP FUNCTION IF EXISTS check_user_balance();
DROP FUNCTION IF EXISTS prevent_ledger_modification();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS sync_state CASCADE;
DROP TABLE IF EXISTS extropy_ledger CASCADE;
DROP TABLE IF EXISTS attributions CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS users CASCADE;
