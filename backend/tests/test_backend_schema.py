"""
Tests for Backend module database schema.

Tests cover:
- Table creation and structure
- DECIMAL precision for $EXTROPY balances
- Negative balance prevention (CHECK constraints and triggers)
- Ledger immutability (triggers)
- Foreign key constraints
- Indexes
"""

import os
from decimal import Decimal
from uuid import uuid4

import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture(scope="session")
def db_connection():
    """Create test database connection."""
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "test_unified_scraper"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }

    conn = psycopg2.connect(**db_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    yield conn

    conn.close()


@pytest.fixture(scope="session", autouse=True)
def setup_schema(db_connection):
    """Apply schema before running tests."""
    schema_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "db",
        "schema.sql"
    )

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    cursor = db_connection.cursor()
    cursor.execute(schema_sql)
    cursor.close()

    yield

    # Cleanup after all tests (optional)


@pytest.fixture
def cursor(db_connection):
    """Get a cursor for each test."""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


@pytest.fixture
def clean_backend_tables(cursor):
    """Clean Backend tables before each test."""
    tables = ['sync_state', 'extropy_ledger', 'attributions', 'cards', 'users']
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
    yield


class TestUsersTable:
    """Tests for users table."""

    def test_users_table_exists(self, cursor):
        """Verify users table exists with correct structure."""
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()

        expected_columns = [
            ('id', 'uuid', 'NO'),
            ('username', 'character varying', 'NO'),
            ('email', 'character varying', 'NO'),
            ('display_name', 'character varying', 'YES'),
            ('bio', 'text', 'YES'),
            ('avatar_url', 'text', 'YES'),
            ('extropy_balance', 'numeric', 'NO'),
            ('api_key_hash', 'character varying', 'YES'),
            ('metadata', 'jsonb', 'YES'),
            ('created_at', 'timestamp without time zone', 'NO'),
            ('updated_at', 'timestamp without time zone', 'NO'),
            ('last_login_at', 'timestamp without time zone', 'YES'),
        ]

        column_names = [(col[0], col[1], col[2]) for col in columns]
        assert len(column_names) == len(expected_columns), f"Expected {len(expected_columns)} columns, got {len(column_names)}"

    def test_extropy_balance_is_decimal(self, cursor, clean_backend_tables):
        """Verify extropy_balance uses DECIMAL (not FLOAT)."""
        cursor.execute("""
            SELECT data_type, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'extropy_balance'
        """)
        data_type, precision, scale = cursor.fetchone()

        assert data_type == 'numeric', "extropy_balance must be NUMERIC (DECIMAL)"
        assert precision == 20, "extropy_balance precision should be 20"
        assert scale == 8, "extropy_balance scale should be 8"

    def test_negative_balance_check_constraint(self, cursor, clean_backend_tables):
        """Verify CHECK constraint prevents negative balances."""
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            cursor.execute("""
                INSERT INTO users (username, email, extropy_balance)
                VALUES ('testuser', 'test@example.com', -10.00)
            """)

        assert "extropy_balance" in str(exc_info.value).lower()

    def test_negative_balance_trigger(self, cursor, clean_backend_tables):
        """Verify trigger prevents negative balances on update."""
        # Insert valid user
        cursor.execute("""
            INSERT INTO users (username, email, extropy_balance)
            VALUES ('testuser', 'test@example.com', 100.00)
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        # Try to update to negative balance
        with pytest.raises(psycopg2.Error) as exc_info:
            cursor.execute("""
                UPDATE users
                SET extropy_balance = -50.00
                WHERE id = %s
            """, (user_id,))

        assert "negative" in str(exc_info.value).lower()

    def test_decimal_precision(self, cursor, clean_backend_tables):
        """Verify DECIMAL maintains precision for small amounts."""
        cursor.execute("""
            INSERT INTO users (username, email, extropy_balance)
            VALUES ('testuser', 'test@example.com', 0.00000001)
            RETURNING extropy_balance
        """)
        balance = cursor.fetchone()[0]

        assert balance == Decimal('0.00000001'), "DECIMAL should maintain 8 decimal places"

    def test_unique_username_constraint(self, cursor, clean_backend_tables):
        """Verify username uniqueness constraint."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test1@example.com')
        """)

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO users (username, email)
                VALUES ('testuser', 'test2@example.com')
            """)


class TestCardsTable:
    """Tests for cards table."""

    def test_cards_table_exists(self, cursor):
        """Verify cards table exists."""
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'cards'
        """)
        assert cursor.fetchone()[0] == 1

    def test_privacy_level_constraint(self, cursor, clean_backend_tables):
        """Verify privacy_level CHECK constraint."""
        # Insert user first
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        # Valid privacy level
        cursor.execute("""
            INSERT INTO cards (user_id, title, body, privacy_level, category)
            VALUES (%s, 'Test Card', 'Test body', 'BUSINESS', 'CATEGORIZED')
        """, (user_id,))

        # Invalid privacy level
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO cards (user_id, title, body, privacy_level, category)
                VALUES (%s, 'Test Card 2', 'Test body', 'INVALID', 'CATEGORIZED')
            """, (user_id,))

    def test_category_constraint(self, cursor, clean_backend_tables):
        """Verify category CHECK constraint."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        # Invalid category
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO cards (user_id, title, body, privacy_level, category)
                VALUES (%s, 'Test Card', 'Test body', 'BUSINESS', 'INVALID_CATEGORY')
            """, (user_id,))

    def test_foreign_key_to_users(self, cursor, clean_backend_tables):
        """Verify foreign key constraint to users table."""
        fake_user_id = uuid4()

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO cards (user_id, title, body, privacy_level, category)
                VALUES (%s, 'Test Card', 'Test body', 'BUSINESS', 'CATEGORIZED')
            """, (fake_user_id,))

    def test_cascade_delete_on_user(self, cursor, clean_backend_tables):
        """Verify cards are deleted when user is deleted."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO cards (user_id, title, body, privacy_level, category)
            VALUES (%s, 'Test Card', 'Test body', 'BUSINESS', 'CATEGORIZED')
            RETURNING id
        """, (user_id,))
        card_id = cursor.fetchone()[0]

        # Delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

        # Verify card is also deleted
        cursor.execute("SELECT COUNT(*) FROM cards WHERE id = %s", (card_id,))
        assert cursor.fetchone()[0] == 0


class TestAttributionsTable:
    """Tests for attributions table."""

    def test_attributions_table_exists(self, cursor):
        """Verify attributions table exists."""
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'attributions'
        """)
        assert cursor.fetchone()[0] == 1

    def test_extropy_transferred_is_decimal(self, cursor):
        """Verify extropy_transferred uses DECIMAL."""
        cursor.execute("""
            SELECT data_type, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'attributions' AND column_name = 'extropy_transferred'
        """)
        data_type, precision, scale = cursor.fetchone()

        assert data_type == 'numeric'
        assert precision == 20
        assert scale == 8

    def test_self_attribution_prevention(self, cursor, clean_backend_tables):
        """Verify a card cannot attribute to itself."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO cards (user_id, title, body, privacy_level, category)
            VALUES (%s, 'Test Card', 'Test body', 'BUSINESS', 'CATEGORIZED')
            RETURNING id
        """, (user_id,))
        card_id = cursor.fetchone()[0]

        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            cursor.execute("""
                INSERT INTO attributions (source_card_id, target_card_id, attribution_type)
                VALUES (%s, %s, 'citation')
            """, (card_id, card_id))

        assert "attribution_different_cards" in str(exc_info.value)

    def test_unique_attribution_constraint(self, cursor, clean_backend_tables):
        """Verify duplicate attributions are prevented."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO cards (user_id, title, body, privacy_level, category)
            VALUES
                (%s, 'Card 1', 'Body 1', 'BUSINESS', 'CATEGORIZED'),
                (%s, 'Card 2', 'Body 2', 'BUSINESS', 'CATEGORIZED')
            RETURNING id
        """, (user_id, user_id))
        card_ids = cursor.fetchall()
        card1_id, card2_id = card_ids[0][0], card_ids[1][0]

        # First attribution
        cursor.execute("""
            INSERT INTO attributions (source_card_id, target_card_id, attribution_type)
            VALUES (%s, %s, 'citation')
        """, (card1_id, card2_id))

        # Duplicate attribution
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO attributions (source_card_id, target_card_id, attribution_type)
                VALUES (%s, %s, 'citation')
            """, (card1_id, card2_id))


class TestExtropyLedger:
    """Tests for extropy_ledger table."""

    def test_ledger_table_exists(self, cursor):
        """Verify extropy_ledger table exists."""
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'extropy_ledger'
        """)
        assert cursor.fetchone()[0] == 1

    def test_amount_is_decimal(self, cursor):
        """Verify amount uses DECIMAL."""
        cursor.execute("""
            SELECT data_type, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'extropy_ledger' AND column_name = 'amount'
        """)
        data_type, precision, scale = cursor.fetchone()

        assert data_type == 'numeric'
        assert precision == 20
        assert scale == 8

    def test_ledger_immutability_update_prevention(self, cursor, clean_backend_tables):
        """Verify ledger entries cannot be updated."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO extropy_ledger (to_user_id, amount, transaction_type, description)
            VALUES (%s, 100.00, 'earn', 'Test transaction')
            RETURNING id
        """, (user_id,))
        ledger_id = cursor.fetchone()[0]

        # Try to update
        with pytest.raises(psycopg2.Error) as exc_info:
            cursor.execute("""
                UPDATE extropy_ledger
                SET amount = 50.00
                WHERE id = %s
            """, (ledger_id,))

        assert "immutable" in str(exc_info.value).lower()

    def test_ledger_immutability_delete_prevention(self, cursor, clean_backend_tables):
        """Verify ledger entries cannot be deleted."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO extropy_ledger (to_user_id, amount, transaction_type, description)
            VALUES (%s, 100.00, 'earn', 'Test transaction')
            RETURNING id
        """, (user_id,))
        ledger_id = cursor.fetchone()[0]

        # Try to delete
        with pytest.raises(psycopg2.Error) as exc_info:
            cursor.execute("""
                DELETE FROM extropy_ledger
                WHERE id = %s
            """, (ledger_id,))

        assert "immutable" in str(exc_info.value).lower()

    def test_positive_amount_constraint(self, cursor, clean_backend_tables):
        """Verify amount must be positive."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO extropy_ledger (to_user_id, amount, transaction_type, description)
                VALUES (%s, -100.00, 'earn', 'Invalid negative transaction')
            """, (user_id,))


class TestSyncState:
    """Tests for sync_state table."""

    def test_sync_state_table_exists(self, cursor):
        """Verify sync_state table exists."""
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'sync_state'
        """)
        assert cursor.fetchone()[0] == 1

    def test_sync_status_constraint(self, cursor, clean_backend_tables):
        """Verify sync_status CHECK constraint."""
        cursor.execute("""
            INSERT INTO users (username, email)
            VALUES ('testuser', 'test@example.com')
            RETURNING id
        """)
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO cards (user_id, title, body, privacy_level, category)
            VALUES (%s, 'Test Card', 'Test body', 'BUSINESS', 'CATEGORIZED')
            RETURNING id
        """, (user_id,))
        card_id = cursor.fetchone()[0]

        # Valid status
        cursor.execute("""
            INSERT INTO sync_state (card_id, user_id, sync_status)
            VALUES (%s, %s, 'pending')
        """, (card_id, user_id))

        # Invalid status
        cursor.execute("""
            INSERT INTO cards (user_id, title, body, privacy_level, category)
            VALUES (%s, 'Test Card 2', 'Test body', 'BUSINESS', 'CATEGORIZED')
            RETURNING id
        """, (user_id,))
        card_id_2 = cursor.fetchone()[0]

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO sync_state (card_id, user_id, sync_status)
                VALUES (%s, %s, 'invalid_status')
            """, (card_id_2, user_id))


class TestIndexes:
    """Tests for database indexes."""

    def test_users_indexes_exist(self, cursor):
        """Verify indexes on users table."""
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'users_pkey',
            'users_username_key',
            'users_email_key',
            'idx_users_username',
            'idx_users_email',
            'idx_users_created_at',
        ]

        for idx in expected_indexes:
            assert idx in indexes, f"Missing index: {idx}"

    def test_cards_indexes_exist(self, cursor):
        """Verify indexes on cards table."""
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'cards'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'cards_pkey',
            'idx_cards_user_id',
            'idx_cards_privacy_level',
            'idx_cards_category',
            'idx_cards_is_published',
        ]

        for idx in expected_indexes:
            assert idx in indexes, f"Missing index: {idx}"

    def test_extropy_ledger_indexes_exist(self, cursor):
        """Verify indexes on extropy_ledger table."""
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'extropy_ledger'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'extropy_ledger_pkey',
            'idx_extropy_ledger_from_user_id',
            'idx_extropy_ledger_to_user_id',
            'idx_extropy_ledger_transaction_type',
        ]

        for idx in expected_indexes:
            assert idx in indexes, f"Missing index: {idx}"
