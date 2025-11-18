# Database Migrations

This directory contains SQL migration files for the Backend module schema.

## Migration Files

### 001_backend_module_schema.sql
Adds the 5 core tables for the Backend module:
- `users` - User accounts with $EXTROPY token balances
- `cards` - Published content cards from Writer module
- `attributions` - Citations, remixes, and replies between cards
- `extropy_ledger` - Immutable transaction log for $EXTROPY tokens
- `sync_state` - Synchronization status tracking for published cards

**Features:**
- DECIMAL precision for $EXTROPY balances (no floating point errors)
- CHECK constraints to prevent negative balances
- Triggers to enforce balance rules and ledger immutability
- Foreign keys with proper cascading
- Comprehensive indexes for query performance
- GIN index on card tags for efficient tag searches

### 001_backend_module_schema_rollback.sql
Rollback script to drop all Backend module tables and related objects.

## Usage

### Apply Migrations

```bash
# Set environment variables (or create .env file)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=unified_scraper
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Apply all migrations
python migrate.py apply
```

### Rollback Migration

```bash
# Rollback a specific migration
python migrate.py rollback 001_backend_module_schema
```

### Manual Application

You can also apply migrations manually using psql:

```bash
# Apply migration
psql -h localhost -U postgres -d unified_scraper -f 001_backend_module_schema.sql

# Rollback migration
psql -h localhost -U postgres -d unified_scraper -f 001_backend_module_schema_rollback.sql
```

## Migration Dependencies

**IMPORTANT:** The Backend module schema depends on the Research module schema being applied first because:
- The `cards` table has an optional foreign key to `contents(id)` from the Research module

Ensure the base schema (`backend/db/schema.sql`) is applied before running Backend module migrations.

## Testing Migrations

After applying migrations, verify tables were created:

```sql
-- List all tables
\dt

-- Check users table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Verify triggers
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_table IN ('users', 'cards', 'extropy_ledger', 'sync_state');

-- Test negative balance prevention
INSERT INTO users (username, email, extropy_balance) VALUES ('test', 'test@example.com', -10.00);
-- Expected: ERROR - User balance cannot be negative

-- Test ledger immutability
INSERT INTO extropy_ledger (to_user_id, amount, transaction_type, description)
VALUES ((SELECT id FROM users LIMIT 1), 100.00, 'earn', 'Test');
UPDATE extropy_ledger SET amount = 50.00 WHERE id = (SELECT id FROM extropy_ledger LIMIT 1);
-- Expected: ERROR - Extropy ledger entries are immutable
```

## Critical Constraints

### DECIMAL Precision
All monetary values use `DECIMAL(20, 8)` instead of `FLOAT` to prevent floating-point precision errors:

```sql
-- ✅ Correct
extropy_balance DECIMAL(20, 8)

-- ❌ Wrong
extropy_balance FLOAT
```

### Negative Balance Prevention
Multiple layers of protection prevent negative balances:
1. CHECK constraint: `CHECK (extropy_balance >= 0)`
2. Trigger: `prevent_negative_balance` - raises exception on insert/update
3. Application-level validation (handled by SIGMA agent)

### Ledger Immutability
The `extropy_ledger` table is append-only:
- UPDATE operations are blocked by trigger
- DELETE operations are blocked by trigger
- Only INSERT is allowed

This ensures complete audit trail of all $EXTROPY transactions.

## Schema Design Principles

1. **Use DECIMAL for money** - Never use FLOAT for currency
2. **Database transactions** - All balance changes must be in transactions
3. **No negative balances** - Enforced at database level
4. **Foreign keys** - Maintain referential integrity
5. **Proper indexes** - Performance optimization
6. **Immutable audit log** - Ledger cannot be modified
7. **Cascading deletes** - Clean up related records automatically

## Next Steps

After applying migrations:
1. RHO agent: Implement authentication endpoints
2. PI agent: Implement publish API
3. SIGMA agent: Implement $EXTROPY token system
4. TAU agent: Implement attribution API
