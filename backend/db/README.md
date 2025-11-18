# Backend Database Schema

PostgreSQL schema for IAC-033 Backend Module supporting Writer publishing, $EXTROPY token system, and attribution tracking.

## Overview

This schema implements 5 core tables:

1. **users** - User accounts with $EXTROPY balances and authentication
2. **cards** - Published content from Writer app with privacy levels
3. **attributions** - Citations, remixes, and replies between cards
4. **extropy_ledger** - Immutable transaction log for $EXTROPY movements
5. **sync_state** - Synchronization tracking between Writer clients and Backend

## Critical Requirements

✅ **DECIMAL for Money** - All $EXTROPY amounts use `DECIMAL(20, 2)` to prevent floating point errors
✅ **No Negative Balances** - Database trigger prevents any transaction resulting in negative balance
✅ **ACID Transactions** - All money operations are atomic and consistent
✅ **Idempotency** - Transaction ledger supports idempotency keys for retry safety
✅ **Audit Trail** - Complete immutable ledger with balance snapshots

## Schema Design

### 1. Users Table

Stores user accounts with $EXTROPY balances.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    extropy_balance DECIMAL(20, 2) NOT NULL DEFAULT 0.00 CHECK (extropy_balance >= 0),
    api_key_hash VARCHAR(255) NOT NULL,
    ...
);
```

**Key Features:**
- UUID primary keys
- bcrypt hashed API keys for authentication
- Balance constraint prevents negative values
- Trigger enforces balance checks on UPDATE

### 2. Cards Table

Published content from Writer app.

```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(1000),
    content TEXT NOT NULL,
    privacy_level VARCHAR(20) CHECK(privacy_level IN ('PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS')),
    category VARCHAR(20) CHECK(category IN ('UNASSIMILATED', 'PROGRAM', 'CATEGORIZED', 'GRIT', 'TOUGH', 'JUNK')),
    extropy_earned DECIMAL(20, 2) DEFAULT 0.00,
    ...
);
```

**Key Features:**
- Privacy levels from Writer app
- Content hash for deduplication
- Public URL and slug generation
- Automatic extropy_earned tracking

### 3. Attributions Table

Track citations and attributions between cards.

```sql
CREATE TABLE attributions (
    id UUID PRIMARY KEY,
    source_card_id UUID REFERENCES cards(id),
    target_card_id UUID REFERENCES cards(id),
    attribution_type VARCHAR(20) CHECK(attribution_type IN ('citation', 'remix', 'reply', 'inspiration')),
    extropy_amount DECIMAL(20, 2) CHECK (extropy_amount >= 0),
    ...
);
```

**Key Features:**
- Tracks source (cited card) and target (citing card)
- $EXTROPY transfer amounts
- Prevents duplicate attributions
- Automatic card.extropy_earned updates via trigger

### 4. Extropy Ledger Table

Immutable transaction log for all $EXTROPY movements.

```sql
CREATE TABLE extropy_ledger (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    transaction_type VARCHAR(50),
    amount DECIMAL(20, 2) NOT NULL,
    balance_before DECIMAL(20, 2) NOT NULL,
    balance_after DECIMAL(20, 2) NOT NULL CHECK (balance_after >= 0),
    idempotency_key VARCHAR(255) UNIQUE,
    ...
);
```

**Transaction Types:**
- `initial_grant` - Starting balance for new users
- `publish_reward` - $EXTROPY earned from publishing a card
- `attribution_payment` - $EXTROPY paid to attribute another card
- `attribution_received` - $EXTROPY received from attribution
- `admin_adjustment` - Manual balance correction
- `bonus` / `penalty` - Other adjustments

**Key Features:**
- Immutable append-only log
- Balance snapshots (before/after)
- Idempotency key for retry safety
- Links to cards and attributions

### 5. Sync State Table

Track synchronization between Writer desktop clients and Backend.

```sql
CREATE TABLE sync_state (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    client_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) CHECK(entity_type IN ('card', 'user_profile', 'settings', 'session')),
    entity_id VARCHAR(255) NOT NULL,
    sync_status VARCHAR(20) CHECK(sync_status IN ('pending', 'synced', 'conflict', 'failed')),
    ...
);
```

**Key Features:**
- Tracks sync state per client
- Checksum-based conflict detection
- Supports push/pull/bidirectional sync
- Retry tracking for failed syncs

## Triggers

### 1. Prevent Negative Balances (CRITICAL)

```sql
CREATE TRIGGER prevent_negative_balance_trigger BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN (NEW.extropy_balance IS DISTINCT FROM OLD.extropy_balance)
    EXECUTE FUNCTION prevent_negative_balance();
```

Prevents any UPDATE that would result in `users.extropy_balance < 0`.

### 2. Auto-Update Card Extropy

```sql
CREATE TRIGGER update_card_extropy_on_attribution AFTER INSERT ON attributions
    FOR EACH ROW EXECUTE FUNCTION update_card_extropy_earned();
```

Automatically updates `cards.extropy_earned` and `cards.attribution_count` when attribution is created.

### 3. Auto-Update Timestamps

```sql
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

Automatically updates `updated_at` timestamp on row modification.

## Views

### 1. user_balance_summary

Comprehensive view of user balances and activity.

```sql
SELECT * FROM user_balance_summary WHERE username = 'alice';
```

Returns: balance, total cards published, total attributions received, total extropy earned.

### 2. recent_transactions

Recent $EXTROPY transactions with context.

```sql
SELECT * FROM recent_transactions WHERE user_id = '...' LIMIT 10;
```

Returns: transaction details with related card/attribution info.

### 3. card_attribution_analytics

Card performance metrics.

```sql
SELECT * FROM card_attribution_analytics WHERE user_id = '...';
```

Returns: card stats, attribution counts, extropy earned per card.

## Migration

### Prerequisites

```bash
# Install psycopg2
pip install psycopg2-binary

# Set DATABASE_URL (optional - defaults to localhost)
export DATABASE_URL="postgresql://user:password@localhost:5432/extrophi_backend"
```

### Apply Schema

```bash
cd backend/db
python migrate.py apply
```

This will:
1. Create database if not exists
2. Apply all tables, triggers, views
3. Insert seed data (system user)
4. Show summary of created objects

### Verify Schema

```bash
python migrate.py verify
```

Checks:
- All 5 tables exist
- All triggers are active
- All views are created
- All DECIMAL fields are correct (not FLOAT)
- Schema version is set

### Check Status

```bash
python migrate.py status
```

Shows:
- Schema version
- Row counts for each table

### Rollback (DANGEROUS)

```bash
python migrate.py rollback
```

Drops all tables. Requires typing 'YES' to confirm.

## Testing

### Test Schema Creation

```bash
# Apply schema
python migrate.py apply

# Verify it worked
python migrate.py verify
```

### Test Negative Balance Prevention

```sql
-- Create test user
INSERT INTO users (username, email, api_key_hash, api_key_prefix, extropy_balance)
VALUES ('test', 'test@example.com', 'hash123', 'ext_test', 100.00);

-- This should SUCCEED (balance stays positive)
UPDATE users SET extropy_balance = 50.00 WHERE username = 'test';

-- This should FAIL (would go negative)
UPDATE users SET extropy_balance = -10.00 WHERE username = 'test';
-- ERROR: Insufficient $EXTROPY balance
```

### Test Transaction Idempotency

```sql
-- First insert succeeds
INSERT INTO extropy_ledger (user_id, transaction_type, amount, balance_before, balance_after, idempotency_key)
VALUES ('...', 'publish_reward', 10.00, 0.00, 10.00, 'unique-key-123');

-- Second insert with same idempotency_key fails
INSERT INTO extropy_ledger (user_id, transaction_type, amount, balance_before, balance_after, idempotency_key)
VALUES ('...', 'publish_reward', 10.00, 0.00, 10.00, 'unique-key-123');
-- ERROR: duplicate key value violates unique constraint
```

## Integration with Writer App

The Writer app (desktop Tauri app) publishes cards to Backend via `POST /api/publish`.

### Publishing Flow

1. User creates content in Writer app (SQLite local database)
2. Content is classified with privacy_level (PRIVATE, PERSONAL, BUSINESS, IDEAS)
3. User selects BUSINESS or IDEAS cards to publish
4. Writer calls `POST /api/publish` with card data
5. Backend:
   - Creates card in `cards` table
   - Awards $EXTROPY via `extropy_ledger`
   - Updates user balance
   - Returns public URL

### Sync Flow

1. Writer client generates unique `client_id` on first run
2. On publish/update, creates `sync_state` record
3. Backend processes sync and updates `sync_status`
4. Writer polls for conflicts and resolves via checksums

## Security Considerations

1. **API Keys**: Stored as bcrypt hashes, never plain text
2. **Balance Checks**: Enforced at database level via triggers
3. **Idempotency**: Prevents duplicate transactions on retry
4. **Checksums**: SHA-256 for content integrity and conflict detection
5. **Cascade Deletes**: Cleanup attribution/ledger on user/card deletion

## Performance

### Indexes

All tables have strategic indexes:
- Primary keys (UUIDs)
- Foreign keys
- Common query patterns (user_id, created_at, status fields)
- Composite indexes for common joins

### Query Optimization

Use views for complex queries:
```sql
-- Instead of complex JOINs
SELECT * FROM user_balance_summary WHERE username = 'alice';

-- Instead of manual aggregation
SELECT * FROM card_attribution_analytics WHERE card_id = '...';
```

## Schema Version

Current version: **1.0.0**

Track in `schema_metadata` table:
```sql
SELECT * FROM schema_metadata;
```

## Maintenance

### Backup

```bash
pg_dump -U postgres extrophi_backend > backup.sql
```

### Restore

```bash
psql -U postgres extrophi_backend < backup.sql
```

### Monitor Balance Integrity

```sql
-- Check for any balance mismatches
SELECT
    u.id,
    u.username,
    u.extropy_balance as current_balance,
    (
        SELECT balance_after
        FROM extropy_ledger
        WHERE user_id = u.id
        ORDER BY created_at DESC
        LIMIT 1
    ) as ledger_balance
FROM users u
WHERE u.extropy_balance != (
    SELECT COALESCE(balance_after, 0)
    FROM extropy_ledger
    WHERE user_id = u.id
    ORDER BY created_at DESC
    LIMIT 1
);
```

Should return 0 rows if integrity is maintained.

## Troubleshooting

### Connection Failed

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

### Schema Already Exists

```bash
# Check existing tables
python migrate.py status

# If needed, rollback and reapply
python migrate.py rollback
python migrate.py apply
```

### Negative Balance Error

This is **intentional**. The trigger prevents insufficient balance transactions.

Fix by ensuring balance checks in application code BEFORE attempting database update.

## Next Steps

After schema is applied:

1. **Agent RHO**: Implement API key authentication
2. **Agent PI**: Build `POST /api/publish` endpoint
3. **Agent SIGMA**: Implement $EXTROPY token operations
4. **Agent TAU**: Build attribution API endpoints

## References

- Technical Proposal: `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`
- Writer Schema: `/writer/src-tauri/src/db/schema.sql`
- Research Schema: `/backend/db/schema.sql` (original, for scraper module)
