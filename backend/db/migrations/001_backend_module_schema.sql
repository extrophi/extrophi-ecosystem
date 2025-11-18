-- Migration: 001 - Backend Module Schema
-- Description: Add 5 tables for Backend module (users, cards, attributions, extropy_ledger, sync_state)
-- Date: 2025-11-18
-- Author: OMICRON Agent
-- Dependencies: Research module schema must be applied first (for contents table)

-- ============================================================================
-- BACKEND MODULE SCHEMA
-- Tables for Writer integration, $EXTROPY token system, and attribution tracking
-- ============================================================================

-- Users table: Store user accounts with $EXTROPY token balances
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(500),
    bio TEXT,
    avatar_url TEXT,

    -- $EXTROPY token balance (DECIMAL for precise money handling)
    extropy_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.00000000 CHECK (extropy_balance >= 0),

    -- API authentication
    api_key_hash VARCHAR(255),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Create indices for users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Cards table: Published content from Writer module
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Card content
    title VARCHAR(1000) NOT NULL,
    body TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',

    -- Privacy level from Writer
    privacy_level VARCHAR(50) NOT NULL CHECK (privacy_level IN ('PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS')),

    -- Card category from Writer
    category VARCHAR(50) NOT NULL CHECK (category IN ('UNASSIMILATED', 'PROGRAM', 'CATEGORIZED', 'GRIT', 'TOUGH', 'JUNK')),

    -- Source information (if card is derived from scraped content)
    source_platform VARCHAR(50),
    source_url TEXT,
    content_id UUID REFERENCES contents(id) ON DELETE SET NULL,

    -- Relationships
    parent_card_id UUID REFERENCES cards(id) ON DELETE SET NULL,
    related_card_ids UUID[] DEFAULT '{}',

    -- Publishing status
    is_published BOOLEAN DEFAULT FALSE,
    published_url TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

-- Create indices for cards
CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_privacy_level ON cards(privacy_level);
CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_cards_is_published ON cards(is_published);
CREATE INDEX IF NOT EXISTS idx_cards_content_id ON cards(content_id);
CREATE INDEX IF NOT EXISTS idx_cards_parent_card_id ON cards(parent_card_id);
CREATE INDEX IF NOT EXISTS idx_cards_created_at ON cards(created_at);
CREATE INDEX IF NOT EXISTS idx_cards_published_at ON cards(published_at);
CREATE INDEX IF NOT EXISTS idx_cards_user_published ON cards(user_id, is_published);
CREATE INDEX IF NOT EXISTS idx_cards_tags ON cards USING GIN (tags);

-- Attributions table: Track citations, remixes, and replies between cards
CREATE TABLE IF NOT EXISTS attributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source and target cards
    source_card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    target_card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,

    -- Attribution type
    attribution_type VARCHAR(50) NOT NULL CHECK (attribution_type IN ('citation', 'remix', 'reply', 'reference')),

    -- Details
    context TEXT,
    excerpt TEXT,

    -- $EXTROPY transfer on attribution
    extropy_transferred DECIMAL(20, 8) DEFAULT 0.00000000 CHECK (extropy_transferred >= 0),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Ensure a card doesn't attribute to itself
    CONSTRAINT attribution_different_cards CHECK (source_card_id != target_card_id),

    -- Prevent duplicate attributions
    CONSTRAINT attribution_unique UNIQUE (source_card_id, target_card_id, attribution_type)
);

-- Create indices for attributions
CREATE INDEX IF NOT EXISTS idx_attributions_source_card_id ON attributions(source_card_id);
CREATE INDEX IF NOT EXISTS idx_attributions_target_card_id ON attributions(target_card_id);
CREATE INDEX IF NOT EXISTS idx_attributions_attribution_type ON attributions(attribution_type);
CREATE INDEX IF NOT EXISTS idx_attributions_created_at ON attributions(created_at);
CREATE INDEX IF NOT EXISTS idx_attributions_source_type ON attributions(source_card_id, attribution_type);
CREATE INDEX IF NOT EXISTS idx_attributions_target_type ON attributions(target_card_id, attribution_type);

-- $EXTROPY ledger table: Immutable transaction log for all token operations
CREATE TABLE IF NOT EXISTS extropy_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Transaction participants
    from_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Transaction details
    amount DECIMAL(20, 8) NOT NULL CHECK (amount > 0),
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('earn', 'transfer', 'reward', 'attribution')),

    -- Related entities
    card_id UUID REFERENCES cards(id) ON DELETE SET NULL,
    attribution_id UUID REFERENCES attributions(id) ON DELETE SET NULL,

    -- Balances after transaction (for audit trail)
    from_user_balance_after DECIMAL(20, 8),
    to_user_balance_after DECIMAL(20, 8),

    -- Description
    description TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamp (immutable - no updates allowed)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- At least one user must be involved
    CONSTRAINT ledger_has_user CHECK (from_user_id IS NOT NULL OR to_user_id IS NOT NULL)
);

-- Create indices for extropy_ledger
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_from_user_id ON extropy_ledger(from_user_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_to_user_id ON extropy_ledger(to_user_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_transaction_type ON extropy_ledger(transaction_type);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_card_id ON extropy_ledger(card_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_attribution_id ON extropy_ledger(attribution_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_created_at ON extropy_ledger(created_at);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_from_user_created ON extropy_ledger(from_user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_to_user_created ON extropy_ledger(to_user_id, created_at);

-- Sync state table: Track synchronization status for published cards
CREATE TABLE IF NOT EXISTS sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL UNIQUE REFERENCES cards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Sync status
    sync_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (sync_status IN ('pending', 'in_progress', 'synced', 'failed')),

    -- Git information (for selective Git publish)
    git_commit_hash VARCHAR(255),
    git_branch VARCHAR(255),
    git_remote_url TEXT,

    -- Sync timestamps
    last_sync_attempt_at TIMESTAMP,
    last_synced_at TIMESTAMP,

    -- Error tracking
    error_count INTEGER DEFAULT 0,
    last_error TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for sync_state
CREATE INDEX IF NOT EXISTS idx_sync_state_card_id ON sync_state(card_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_user_id ON sync_state(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_sync_status ON sync_state(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_state_last_synced_at ON sync_state(last_synced_at);
CREATE INDEX IF NOT EXISTS idx_sync_state_user_status ON sync_state(user_id, sync_status);

-- ============================================================================
-- TRIGGERS FOR BACKEND MODULE
-- ============================================================================

-- Trigger to update updated_at on users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at on cards table
DROP TRIGGER IF EXISTS update_cards_updated_at ON cards;
CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at on sync_state table
DROP TRIGGER IF EXISTS update_sync_state_updated_at ON sync_state;
CREATE TRIGGER update_sync_state_updated_at BEFORE UPDATE ON sync_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to prevent negative balances on users table
CREATE OR REPLACE FUNCTION check_user_balance()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.extropy_balance < 0 THEN
        RAISE EXCEPTION 'User balance cannot be negative. Attempted balance: %', NEW.extropy_balance;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_negative_balance ON users;
CREATE TRIGGER prevent_negative_balance BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION check_user_balance();

-- Trigger to prevent updates to extropy_ledger (immutable log)
CREATE OR REPLACE FUNCTION prevent_ledger_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Extropy ledger entries are immutable and cannot be modified';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_extropy_ledger_update ON extropy_ledger;
CREATE TRIGGER prevent_extropy_ledger_update BEFORE UPDATE ON extropy_ledger
    FOR EACH ROW EXECUTE FUNCTION prevent_ledger_modification();

DROP TRIGGER IF EXISTS prevent_extropy_ledger_delete ON extropy_ledger;
CREATE TRIGGER prevent_extropy_ledger_delete BEFORE DELETE ON extropy_ledger
    FOR EACH ROW EXECUTE FUNCTION prevent_ledger_modification();

-- ============================================================================
-- COMMENTS FOR BACKEND MODULE TABLES
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts with $EXTROPY token balances and API authentication';
COMMENT ON TABLE cards IS 'Published content cards from Writer module with privacy levels and categories';
COMMENT ON TABLE attributions IS 'Citations, remixes, and replies between cards with $EXTROPY attribution transfers';
COMMENT ON TABLE extropy_ledger IS 'Immutable transaction log for all $EXTROPY token operations';
COMMENT ON TABLE sync_state IS 'Synchronization status tracking for published cards (Git integration)';

COMMENT ON COLUMN users.extropy_balance IS '$EXTROPY token balance (DECIMAL for precise handling, CHECK constraint prevents negatives)';
COMMENT ON COLUMN users.api_key_hash IS 'Hashed API key for authentication (never store plain text)';
COMMENT ON COLUMN cards.privacy_level IS 'Privacy classification from Writer: PRIVATE, PERSONAL, BUSINESS, IDEAS';
COMMENT ON COLUMN cards.category IS 'Card category from Writer: UNASSIMILATED, PROGRAM, CATEGORIZED, GRIT, TOUGH, JUNK';
COMMENT ON COLUMN cards.content_id IS 'Foreign key to scraped content if card is derived from research';
COMMENT ON COLUMN attributions.attribution_type IS 'Type of attribution: citation, remix, reply, reference';
COMMENT ON COLUMN attributions.extropy_transferred IS '$EXTROPY tokens transferred on attribution';
COMMENT ON COLUMN extropy_ledger.amount IS 'Transaction amount (DECIMAL, always positive)';
COMMENT ON COLUMN extropy_ledger.transaction_type IS 'Transaction type: earn, transfer, reward, attribution';
COMMENT ON COLUMN extropy_ledger.from_user_balance_after IS 'Sender balance after transaction (audit trail)';
COMMENT ON COLUMN extropy_ledger.to_user_balance_after IS 'Receiver balance after transaction (audit trail)';
COMMENT ON COLUMN sync_state.sync_status IS 'Sync status: pending, in_progress, synced, failed';
COMMENT ON COLUMN sync_state.git_commit_hash IS 'Git commit hash from selective publish';
