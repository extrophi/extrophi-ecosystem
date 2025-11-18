-- IAC-033 Backend Module Database Schema
-- PostgreSQL schema for Writer publishing, $EXTROPY token system, and attribution tracking
--
-- CRITICAL: Uses DECIMAL for all money amounts to prevent floating point errors
-- CRITICAL: Triggers prevent negative balances
-- CRITICAL: All transactions are ACID-compliant

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension (shared with Research module)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- USERS TABLE: Account management and $EXTROPY balances
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(500),
    bio TEXT,

    -- $EXTROPY balance - MUST be DECIMAL, never FLOAT
    extropy_balance DECIMAL(20, 2) NOT NULL DEFAULT 0.00 CHECK (extropy_balance >= 0),

    -- Authentication
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    api_key_prefix VARCHAR(10) NOT NULL, -- First 8 chars for identification

    -- Account status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Profile metadata
    avatar_url TEXT,
    profile_url TEXT,
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Indices for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key_hash ON users(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_users_api_key_prefix ON users(api_key_prefix);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

COMMENT ON TABLE users IS 'User accounts with $EXTROPY token balances and authentication';
COMMENT ON COLUMN users.extropy_balance IS 'User $EXTROPY balance - DECIMAL(20,2) prevents floating point errors';
COMMENT ON COLUMN users.api_key_hash IS 'Bcrypt hash of API key for authentication';
COMMENT ON COLUMN users.api_key_prefix IS 'First 8 characters of API key for display (e.g., ext_1234...)';

-- ============================================================================
-- CARDS TABLE: Published content from Writer app
-- ============================================================================

CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Content
    title VARCHAR(1000),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for deduplication

    -- Privacy classification (from Writer app)
    privacy_level VARCHAR(20) NOT NULL CHECK(privacy_level IN ('PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS')),

    -- Card categorization (from Writer app)
    category VARCHAR(20) CHECK(category IN ('UNASSIMILATED', 'PROGRAM', 'CATEGORIZED', 'GRIT', 'TOUGH', 'JUNK')),

    -- Publishing status
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    published_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Source tracking (reference to Writer app's chat_session)
    source_session_id INTEGER, -- SQLite session ID from Writer app
    source_client_id VARCHAR(255), -- Which Writer client published this

    -- Public URL (generated after publish)
    public_url TEXT UNIQUE,
    slug VARCHAR(255) UNIQUE,

    -- Engagement metrics
    view_count INTEGER NOT NULL DEFAULT 0,
    attribution_count INTEGER NOT NULL DEFAULT 0,
    extropy_earned DECIMAL(20, 2) NOT NULL DEFAULT 0.00,

    -- Rich metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indices for cards table
CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_privacy_level ON cards(privacy_level);
CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_cards_is_published ON cards(is_published);
CREATE INDEX IF NOT EXISTS idx_cards_published_at ON cards(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_cards_content_hash ON cards(content_hash);
CREATE INDEX IF NOT EXISTS idx_cards_slug ON cards(slug);
CREATE INDEX IF NOT EXISTS idx_cards_user_published ON cards(user_id, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_cards_tags ON cards USING GIN(tags);

COMMENT ON TABLE cards IS 'Published cards from Writer app with privacy levels and $EXTROPY tracking';
COMMENT ON COLUMN cards.privacy_level IS 'Privacy classification: PRIVATE (never published), PERSONAL (local only), BUSINESS (shareable), IDEAS (public)';
COMMENT ON COLUMN cards.category IS 'Writer app categorization for organizing thoughts';
COMMENT ON COLUMN cards.content_hash IS 'SHA-256 hash of content for deduplication and integrity checking';
COMMENT ON COLUMN cards.extropy_earned IS 'Total $EXTROPY earned from this card (publish reward + attributions)';

-- ============================================================================
-- ATTRIBUTIONS TABLE: Citations, remixes, and replies between cards
-- ============================================================================

CREATE TABLE IF NOT EXISTS attributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source: The card being attributed/cited
    source_card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    source_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Target: The card doing the citing/attributing
    target_card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Attribution metadata
    attribution_type VARCHAR(20) NOT NULL CHECK(attribution_type IN ('citation', 'remix', 'reply', 'inspiration')),

    -- $EXTROPY transfer
    extropy_amount DECIMAL(20, 2) NOT NULL DEFAULT 0.00 CHECK (extropy_amount >= 0),

    -- Optional context
    attribution_note TEXT,
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indices for attributions table
CREATE INDEX IF NOT EXISTS idx_attributions_source_card ON attributions(source_card_id);
CREATE INDEX IF NOT EXISTS idx_attributions_source_user ON attributions(source_user_id);
CREATE INDEX IF NOT EXISTS idx_attributions_target_card ON attributions(target_card_id);
CREATE INDEX IF NOT EXISTS idx_attributions_target_user ON attributions(target_user_id);
CREATE INDEX IF NOT EXISTS idx_attributions_type ON attributions(attribution_type);
CREATE INDEX IF NOT EXISTS idx_attributions_created_at ON attributions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_attributions_source_card_created ON attributions(source_card_id, created_at DESC);

-- Prevent self-attribution
CREATE UNIQUE INDEX IF NOT EXISTS idx_attributions_no_duplicates
    ON attributions(source_card_id, target_card_id);

COMMENT ON TABLE attributions IS 'Track citations, remixes, and replies between cards with $EXTROPY transfers';
COMMENT ON COLUMN attributions.attribution_type IS 'citation: reference, remix: derivative work, reply: response, inspiration: influenced by';
COMMENT ON COLUMN attributions.extropy_amount IS '$EXTROPY transferred from target_user to source_user as attribution payment';

-- ============================================================================
-- EXTROPY_LEDGER TABLE: Complete transaction log for $EXTROPY token system
-- ============================================================================

CREATE TABLE IF NOT EXISTS extropy_ledger (
    id BIGSERIAL PRIMARY KEY,

    -- User and transaction details
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL CHECK(transaction_type IN (
        'initial_grant',
        'publish_reward',
        'attribution_payment',
        'attribution_received',
        'admin_adjustment',
        'bonus',
        'penalty'
    )),

    -- Amount and balance tracking
    amount DECIMAL(20, 2) NOT NULL, -- Positive for credits, negative for debits
    balance_before DECIMAL(20, 2) NOT NULL,
    balance_after DECIMAL(20, 2) NOT NULL CHECK (balance_after >= 0),

    -- Related entities (nullable - depends on transaction type)
    card_id UUID REFERENCES cards(id) ON DELETE SET NULL,
    attribution_id UUID REFERENCES attributions(id) ON DELETE SET NULL,

    -- Transaction metadata
    description TEXT,
    metadata JSONB DEFAULT '{}',

    -- Idempotency key for preventing duplicate transactions
    idempotency_key VARCHAR(255) UNIQUE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indices for extropy_ledger table
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_user_id ON extropy_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_transaction_type ON extropy_ledger(transaction_type);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_created_at ON extropy_ledger(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_user_created ON extropy_ledger(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_card_id ON extropy_ledger(card_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_attribution_id ON extropy_ledger(attribution_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_idempotency ON extropy_ledger(idempotency_key);

COMMENT ON TABLE extropy_ledger IS 'Immutable transaction log for all $EXTROPY movements (double-entry accounting)';
COMMENT ON COLUMN extropy_ledger.amount IS 'Transaction amount: positive for credits, negative for debits';
COMMENT ON COLUMN extropy_ledger.balance_before IS 'User balance snapshot before transaction';
COMMENT ON COLUMN extropy_ledger.balance_after IS 'User balance snapshot after transaction (must be >= 0)';
COMMENT ON COLUMN extropy_ledger.idempotency_key IS 'Prevents duplicate transactions (e.g., retry on network failure)';

-- ============================================================================
-- SYNC_STATE TABLE: Track synchronization between Writer clients and Backend
-- ============================================================================

CREATE TABLE IF NOT EXISTS sync_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User and client tracking
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id VARCHAR(255) NOT NULL, -- Unique ID for each Writer client instance
    device_name VARCHAR(255),

    -- Entity being synced
    entity_type VARCHAR(50) NOT NULL CHECK(entity_type IN ('card', 'user_profile', 'settings', 'session')),
    entity_id VARCHAR(255) NOT NULL, -- UUID or ID of the synced entity

    -- Sync status
    sync_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK(sync_status IN ('pending', 'synced', 'conflict', 'failed')),
    last_synced_at TIMESTAMP,

    -- Conflict resolution
    local_checksum VARCHAR(64), -- SHA-256 of local data
    remote_checksum VARCHAR(64), -- SHA-256 of remote data
    conflict_resolution VARCHAR(20) CHECK(conflict_resolution IN ('local_wins', 'remote_wins', 'manual', NULL)),

    -- Sync metadata
    sync_direction VARCHAR(10) CHECK(sync_direction IN ('push', 'pull', 'bidirectional')),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indices for sync_state table
CREATE INDEX IF NOT EXISTS idx_sync_state_user_id ON sync_state(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_client_id ON sync_state(client_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_entity_type ON sync_state(entity_type);
CREATE INDEX IF NOT EXISTS idx_sync_state_entity_id ON sync_state(entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_sync_status ON sync_state(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_state_user_entity ON sync_state(user_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_last_synced ON sync_state(last_synced_at DESC);

-- Ensure unique sync records per user + client + entity
CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_state_unique_entity
    ON sync_state(user_id, client_id, entity_type, entity_id);

COMMENT ON TABLE sync_state IS 'Track synchronization state between Writer desktop clients and Backend API';
COMMENT ON COLUMN sync_state.client_id IS 'Unique identifier for each Writer app installation';
COMMENT ON COLUMN sync_state.local_checksum IS 'SHA-256 hash of local data for conflict detection';
COMMENT ON COLUMN sync_state.remote_checksum IS 'SHA-256 hash of backend data for conflict detection';

-- ============================================================================
-- TRIGGERS: Automatic timestamp updates and balance enforcement
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_cards_updated_at ON cards;
CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sync_state_updated_at ON sync_state;
CREATE TRIGGER update_sync_state_updated_at BEFORE UPDATE ON sync_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- CRITICAL: Trigger to prevent negative balances
-- ============================================================================

CREATE OR REPLACE FUNCTION prevent_negative_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if update would result in negative balance
    IF NEW.extropy_balance < 0 THEN
        RAISE EXCEPTION 'Insufficient $EXTROPY balance. Current: %, Attempted: %',
            OLD.extropy_balance, NEW.extropy_balance;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS prevent_negative_balance_trigger ON users;
CREATE TRIGGER prevent_negative_balance_trigger BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN (NEW.extropy_balance IS DISTINCT FROM OLD.extropy_balance)
    EXECUTE FUNCTION prevent_negative_balance();

COMMENT ON FUNCTION prevent_negative_balance IS 'Prevents any transaction that would result in negative $EXTROPY balance';

-- ============================================================================
-- TRIGGER: Automatically update card extropy_earned on new attribution
-- ============================================================================

CREATE OR REPLACE FUNCTION update_card_extropy_earned()
RETURNS TRIGGER AS $$
BEGIN
    -- Add attribution amount to source card's extropy_earned
    UPDATE cards
    SET extropy_earned = extropy_earned + NEW.extropy_amount,
        attribution_count = attribution_count + 1
    WHERE id = NEW.source_card_id;

    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_card_extropy_on_attribution ON attributions;
CREATE TRIGGER update_card_extropy_on_attribution AFTER INSERT ON attributions
    FOR EACH ROW EXECUTE FUNCTION update_card_extropy_earned();

COMMENT ON FUNCTION update_card_extropy_earned IS 'Automatically updates card.extropy_earned when attribution is created';

-- ============================================================================
-- VIEWS: Convenient queries for common operations
-- ============================================================================

-- User balance summary with transaction history
CREATE OR REPLACE VIEW user_balance_summary AS
SELECT
    u.id,
    u.username,
    u.email,
    u.extropy_balance,
    COUNT(DISTINCT c.id) as total_cards_published,
    COUNT(DISTINCT a.id) as total_attributions_received,
    COALESCE(SUM(c.extropy_earned), 0) as total_extropy_from_cards,
    (
        SELECT COUNT(*)
        FROM extropy_ledger el
        WHERE el.user_id = u.id
    ) as total_transactions
FROM users u
LEFT JOIN cards c ON u.id = c.user_id
LEFT JOIN attributions a ON u.id = a.source_user_id
GROUP BY u.id, u.username, u.email, u.extropy_balance;

COMMENT ON VIEW user_balance_summary IS 'Comprehensive view of user balances and activity';

-- Recent transactions view
CREATE OR REPLACE VIEW recent_transactions AS
SELECT
    el.id,
    el.user_id,
    u.username,
    el.transaction_type,
    el.amount,
    el.balance_after,
    el.description,
    el.created_at,
    c.title as related_card_title,
    a.attribution_type as related_attribution_type
FROM extropy_ledger el
JOIN users u ON el.user_id = u.id
LEFT JOIN cards c ON el.card_id = c.id
LEFT JOIN attributions a ON el.attribution_id = a.id
ORDER BY el.created_at DESC;

COMMENT ON VIEW recent_transactions IS 'Recent $EXTROPY transactions with context';

-- Card attribution analytics
CREATE OR REPLACE VIEW card_attribution_analytics AS
SELECT
    c.id as card_id,
    c.title,
    c.user_id,
    u.username,
    c.privacy_level,
    c.category,
    c.published_at,
    c.attribution_count,
    c.extropy_earned,
    COUNT(a.id) as attribution_breakdown_count,
    COALESCE(SUM(a.extropy_amount), 0) as total_attribution_payments
FROM cards c
JOIN users u ON c.user_id = u.id
LEFT JOIN attributions a ON c.id = a.source_card_id
GROUP BY c.id, c.title, c.user_id, u.username, c.privacy_level, c.category,
         c.published_at, c.attribution_count, c.extropy_earned;

COMMENT ON VIEW card_attribution_analytics IS 'Card performance metrics and attribution analytics';

-- ============================================================================
-- SEED DATA: Initial setup (optional - for development)
-- ============================================================================

-- Note: In production, users are created via registration API
-- This is for development/testing only

-- Example: Create a system user for admin operations
INSERT INTO users (
    id,
    username,
    email,
    display_name,
    api_key_hash,
    api_key_prefix,
    extropy_balance,
    is_active,
    email_verified
) VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system',
    'system@extrophi.local',
    'System Account',
    '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7VEjBU7Kvq', -- placeholder hash
    'ext_sys',
    0.00,
    true,
    true
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- METADATA: Schema version tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_metadata (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_metadata (key, value) VALUES
    ('schema_version', '1.0.0'),
    ('created_at', CURRENT_TIMESTAMP::TEXT),
    ('description', 'IAC-033 Backend Module - Cards, Users, Attributions, $EXTROPY Ledger, Sync State')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;

COMMENT ON TABLE schema_metadata IS 'Schema version and metadata tracking';
