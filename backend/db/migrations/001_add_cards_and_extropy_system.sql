-- Migration 001: Add Cards, Users, Attributions, and $EXTROPY Ledger System
-- Created: 2025-11-18
-- Description: Adds the core tables for the BrainDump publishing system with $EXTROPY token economy
-- Dependencies: Requires PostgreSQL 14+ and uuid-ossp extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE
-- Stores user accounts with API key authentication and $EXTROPY balances
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    api_key_hash TEXT NOT NULL UNIQUE,
    extropy_balance DECIMAL(20, 8) NOT NULL DEFAULT 0 CHECK(extropy_balance >= 0),
    total_earned DECIMAL(20, 8) NOT NULL DEFAULT 0,
    total_spent DECIMAL(20, 8) NOT NULL DEFAULT 0,
    card_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key_hash ON users(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_users_extropy_balance ON users(extropy_balance);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- CARDS TABLE
-- Stores published cards from BrainDump with content, privacy levels, and git tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    title TEXT,
    category TEXT,
    privacy_level TEXT NOT NULL DEFAULT 'private' CHECK(privacy_level IN ('private', 'unlisted', 'public')),
    published BOOLEAN NOT NULL DEFAULT FALSE,
    git_sha TEXT,
    git_repo_url TEXT,
    source_session_id TEXT,
    word_count INTEGER,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for cards
CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_privacy_level ON cards(privacy_level);
CREATE INDEX IF NOT EXISTS idx_cards_published ON cards(published) WHERE published = TRUE;
CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_cards_git_sha ON cards(git_sha);
CREATE INDEX IF NOT EXISTS idx_cards_created_at ON cards(created_at);
CREATE INDEX IF NOT EXISTS idx_cards_published_at ON cards(published_at);
CREATE INDEX IF NOT EXISTS idx_cards_tags ON cards USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_cards_user_published ON cards(user_id, published) WHERE published = TRUE;

-- Full-text search index on card content
CREATE INDEX IF NOT EXISTS idx_cards_content_fts ON cards USING GIN(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_cards_title_fts ON cards USING GIN(to_tsvector('english', coalesce(title, '')));

-- ============================================================================
-- ATTRIBUTIONS TABLE
-- Tracks citations, remixes, and replies between cards with $EXTROPY rewards
-- ============================================================================
CREATE TABLE IF NOT EXISTS attributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    target_card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    attribution_type TEXT NOT NULL CHECK(attribution_type IN ('citation', 'remix', 'reply')),
    extropy_amount DECIMAL(20, 8) NOT NULL DEFAULT 0 CHECK(extropy_amount >= 0),
    extropy_paid BOOLEAN NOT NULL DEFAULT FALSE,
    citation_context TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    CONSTRAINT attributions_source_target_unique UNIQUE (source_card_id, target_card_id, attribution_type),
    CONSTRAINT attributions_no_self_reference CHECK (source_card_id != target_card_id)
);

-- Create indices for attributions
CREATE INDEX IF NOT EXISTS idx_attributions_source_card_id ON attributions(source_card_id);
CREATE INDEX IF NOT EXISTS idx_attributions_target_card_id ON attributions(target_card_id);
CREATE INDEX IF NOT EXISTS idx_attributions_attribution_type ON attributions(attribution_type);
CREATE INDEX IF NOT EXISTS idx_attributions_extropy_paid ON attributions(extropy_paid) WHERE extropy_paid = FALSE;
CREATE INDEX IF NOT EXISTS idx_attributions_created_at ON attributions(created_at);

-- ============================================================================
-- EXTROPY_LEDGER TABLE
-- Immutable transaction log for all $EXTROPY movements
-- ============================================================================
CREATE TABLE IF NOT EXISTS extropy_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(20, 8) NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('earn', 'transfer', 'burn', 'refund', 'adjustment')),
    reference_id UUID,
    reference_type TEXT CHECK(reference_type IN ('card', 'attribution', 'manual')),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT extropy_ledger_positive_earn CHECK (
        (transaction_type != 'earn' OR amount > 0)
    ),
    CONSTRAINT extropy_ledger_negative_spend CHECK (
        (transaction_type NOT IN ('transfer', 'burn') OR amount < 0)
    )
);

-- Create indices for extropy_ledger
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_user_id ON extropy_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_transaction_type ON extropy_ledger(transaction_type);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_reference_id ON extropy_ledger(reference_id);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_timestamp ON extropy_ledger(timestamp);
CREATE INDEX IF NOT EXISTS idx_extropy_ledger_user_timestamp ON extropy_ledger(user_id, timestamp DESC);

-- ============================================================================
-- SYNC_STATE TABLE
-- Tracks git synchronization state for published cards
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL UNIQUE REFERENCES cards(id) ON DELETE CASCADE,
    last_sync TIMESTAMP,
    sync_status TEXT NOT NULL DEFAULT 'pending' CHECK(sync_status IN ('pending', 'syncing', 'synced', 'failed')),
    sync_error TEXT,
    commits_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for sync_state
CREATE INDEX IF NOT EXISTS idx_sync_state_card_id ON sync_state(card_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_sync_status ON sync_state(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_state_last_sync ON sync_state(last_sync);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger function: Update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_cards_updated_at ON cards;
CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sync_state_updated_at ON sync_state;
CREATE TRIGGER update_sync_state_updated_at BEFORE UPDATE ON sync_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger function: Prevent negative $EXTROPY balances
CREATE OR REPLACE FUNCTION prevent_negative_extropy_balance()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.extropy_balance < 0 THEN
        RAISE EXCEPTION 'Extropy balance cannot be negative. Attempted balance: %', NEW.extropy_balance
            USING HINT = 'Ensure sufficient balance before transfer/burn operations',
                  ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS check_users_extropy_balance ON users;
CREATE TRIGGER check_users_extropy_balance BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION prevent_negative_extropy_balance();

-- Trigger function: Update user card_count on card insert/delete
CREATE OR REPLACE FUNCTION update_user_card_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE users SET card_count = card_count + 1 WHERE id = NEW.user_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE users SET card_count = card_count - 1 WHERE id = OLD.user_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_card_count_insert ON cards;
CREATE TRIGGER update_card_count_insert AFTER INSERT ON cards
    FOR EACH ROW EXECUTE FUNCTION update_user_card_count();

DROP TRIGGER IF EXISTS update_card_count_delete ON cards;
CREATE TRIGGER update_card_count_delete AFTER DELETE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_user_card_count();

-- Trigger function: Update user total_earned on extropy earn transactions
CREATE OR REPLACE FUNCTION update_user_extropy_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.transaction_type = 'earn' THEN
        UPDATE users SET total_earned = total_earned + NEW.amount WHERE id = NEW.user_id;
    ELSIF NEW.transaction_type IN ('transfer', 'burn') THEN
        UPDATE users SET total_spent = total_spent + ABS(NEW.amount) WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_extropy_stats ON extropy_ledger;
CREATE TRIGGER update_extropy_stats AFTER INSERT ON extropy_ledger
    FOR EACH ROW EXECUTE FUNCTION update_user_extropy_stats();

-- Trigger function: Set published_at timestamp when card is published
CREATE OR REPLACE FUNCTION set_published_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.published = TRUE AND OLD.published = FALSE THEN
        NEW.published_at = CURRENT_TIMESTAMP;
    ELSIF NEW.published = FALSE AND OLD.published = TRUE THEN
        NEW.published_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS set_card_published_at ON cards;
CREATE TRIGGER set_card_published_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION set_published_at();

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Transfer $EXTROPY between users with transaction safety
CREATE OR REPLACE FUNCTION transfer_extropy(
    p_from_user_id UUID,
    p_to_user_id UUID,
    p_amount DECIMAL(20, 8),
    p_reference_id UUID DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_from_balance DECIMAL(20, 8);
BEGIN
    -- Validate amount
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Transfer amount must be positive: %', p_amount;
    END IF;

    -- Check sender balance with row lock
    SELECT extropy_balance INTO v_from_balance
    FROM users
    WHERE id = p_from_user_id
    FOR UPDATE;

    IF v_from_balance IS NULL THEN
        RAISE EXCEPTION 'Sender user not found: %', p_from_user_id;
    END IF;

    IF v_from_balance < p_amount THEN
        RAISE EXCEPTION 'Insufficient balance. Available: %, Required: %', v_from_balance, p_amount;
    END IF;

    -- Deduct from sender
    UPDATE users SET extropy_balance = extropy_balance - p_amount WHERE id = p_from_user_id;

    -- Add to recipient
    UPDATE users SET extropy_balance = extropy_balance + p_amount WHERE id = p_to_user_id;

    -- Record debit transaction
    INSERT INTO extropy_ledger (user_id, amount, transaction_type, reference_id, description)
    VALUES (p_from_user_id, -p_amount, 'transfer', p_reference_id, p_description);

    -- Record credit transaction
    INSERT INTO extropy_ledger (user_id, amount, transaction_type, reference_id, description)
    VALUES (p_to_user_id, p_amount, 'earn', p_reference_id, p_description);

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function: Award $EXTROPY for publishing a card
CREATE OR REPLACE FUNCTION award_publish_extropy(
    p_user_id UUID,
    p_card_id UUID,
    p_amount DECIMAL(20, 8) DEFAULT 10.0
) RETURNS BOOLEAN AS $$
BEGIN
    -- Update user balance
    UPDATE users SET extropy_balance = extropy_balance + p_amount WHERE id = p_user_id;

    -- Record transaction
    INSERT INTO extropy_ledger (user_id, amount, transaction_type, reference_id, reference_type, description)
    VALUES (p_user_id, p_amount, 'earn', p_card_id, 'card', 'Published card reward');

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function: Process attribution payment
CREATE OR REPLACE FUNCTION process_attribution_payment(
    p_attribution_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_attribution RECORD;
    v_source_user_id UUID;
    v_target_user_id UUID;
BEGIN
    -- Get attribution details
    SELECT a.*, c.user_id AS target_user_id
    INTO v_attribution
    FROM attributions a
    JOIN cards c ON c.id = a.target_card_id
    WHERE a.id = p_attribution_id
    FOR UPDATE OF a;

    IF v_attribution IS NULL THEN
        RAISE EXCEPTION 'Attribution not found: %', p_attribution_id;
    END IF;

    IF v_attribution.extropy_paid = TRUE THEN
        RAISE EXCEPTION 'Attribution already paid: %', p_attribution_id;
    END IF;

    -- Get source card owner
    SELECT user_id INTO v_source_user_id FROM cards WHERE id = v_attribution.source_card_id;

    -- Transfer extropy
    PERFORM transfer_extropy(
        v_source_user_id,
        v_attribution.target_user_id,
        v_attribution.extropy_amount,
        p_attribution_id,
        'Attribution payment: ' || v_attribution.attribution_type
    );

    -- Mark as paid
    UPDATE attributions SET extropy_paid = TRUE, paid_at = CURRENT_TIMESTAMP WHERE id = p_attribution_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: User statistics summary
CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    u.extropy_balance,
    u.total_earned,
    u.total_spent,
    u.card_count,
    COUNT(DISTINCT c.id) FILTER (WHERE c.published = TRUE) AS published_card_count,
    COUNT(DISTINCT a_source.id) AS attributions_made,
    COUNT(DISTINCT a_target.id) AS attributions_received,
    SUM(a_target.extropy_amount) FILTER (WHERE a_target.extropy_paid = TRUE) AS extropy_from_attributions,
    u.created_at,
    u.updated_at
FROM users u
LEFT JOIN cards c ON c.user_id = u.id
LEFT JOIN attributions a_source ON a_source.source_card_id IN (SELECT id FROM cards WHERE user_id = u.id)
LEFT JOIN attributions a_target ON a_target.target_card_id IN (SELECT id FROM cards WHERE user_id = u.id)
GROUP BY u.id;

-- View: Card details with author info
CREATE OR REPLACE VIEW card_details AS
SELECT
    c.id,
    c.user_id,
    u.username AS author_username,
    c.title,
    c.content,
    c.category,
    c.privacy_level,
    c.published,
    c.git_sha,
    c.git_repo_url,
    c.word_count,
    c.tags,
    COUNT(DISTINCT a_source.id) AS attribution_count,
    COALESCE(SUM(a_source.extropy_amount) FILTER (WHERE a_source.extropy_paid = TRUE), 0) AS extropy_earned_from_attributions,
    c.created_at,
    c.published_at,
    c.updated_at
FROM cards c
JOIN users u ON u.id = c.user_id
LEFT JOIN attributions a_source ON a_source.target_card_id = c.id
GROUP BY c.id, u.username;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts with API key authentication and $EXTROPY token balances';
COMMENT ON TABLE cards IS 'Published cards from BrainDump with content, privacy levels, and git tracking';
COMMENT ON TABLE attributions IS 'Citations, remixes, and replies between cards with $EXTROPY rewards';
COMMENT ON TABLE extropy_ledger IS 'Immutable transaction log for all $EXTROPY movements';
COMMENT ON TABLE sync_state IS 'Git synchronization state tracking for published cards';

COMMENT ON COLUMN users.extropy_balance IS 'Current $EXTROPY balance (DECIMAL for precision, CHECK constraint prevents negative)';
COMMENT ON COLUMN users.api_key_hash IS 'Bcrypt hash of API key for authentication';
COMMENT ON COLUMN cards.privacy_level IS 'Privacy setting: private (owner only), unlisted (link only), public (discoverable)';
COMMENT ON COLUMN cards.git_sha IS 'Git commit SHA if card is published to git repository';
COMMENT ON COLUMN attributions.attribution_type IS 'Type of attribution: citation (quote), remix (derivative), reply (response)';
COMMENT ON COLUMN attributions.extropy_amount IS 'Amount of $EXTROPY to transfer on attribution';
COMMENT ON COLUMN extropy_ledger.transaction_type IS 'earn (reward), transfer (send), burn (destroy), refund, adjustment';
COMMENT ON COLUMN extropy_ledger.amount IS 'Positive for earn, negative for transfer/burn';

COMMENT ON FUNCTION transfer_extropy IS 'Safely transfer $EXTROPY between users with transaction atomicity';
COMMENT ON FUNCTION award_publish_extropy IS 'Award $EXTROPY tokens when a user publishes a card';
COMMENT ON FUNCTION process_attribution_payment IS 'Process $EXTROPY payment for an attribution';
