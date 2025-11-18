"""
Comprehensive tests for API key authentication system.

Tests cover:
- API key generation (secure random, 32+ chars)
- SHA-256 hashed storage (never plaintext)
- Authorization middleware
- Rate limiting (1000 req/hour per key)
- Key management endpoints (create, list, revoke)
"""

import hashlib
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.auth.api_keys import APIKeyAuth
from backend.db.models import (
    APIKeyCreateRequest,
    APIKeyORM,
    Base,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    # Create a test user table (simplified, just for testing)
    with engine.connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                extropy_balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def test_user_id(db_session):
    """Create a test user and return their ID."""
    user_id = str(uuid4())

    # Insert test user directly into SQLite
    db_session.execute(
        f"""
        INSERT INTO users (id, username, email)
        VALUES ('{user_id}', 'testuser', 'test@example.com')
        """
    )
    db_session.commit()

    return user_id


# ============================================================================
# Test: API Key Generation
# ============================================================================


def test_generate_key_format():
    """Test that generated keys have correct format and length."""
    full_key, prefix, key_hash = APIKeyAuth.generate_key()

    # Check key starts with prefix
    assert full_key.startswith("sk_live_")

    # Check key length (should be 32+ chars after prefix)
    assert len(full_key) > 40  # "sk_live_" (8) + 32+ random chars

    # Check prefix extraction
    assert prefix == full_key[:14]
    assert prefix.startswith("sk_live_")

    # Check hash is SHA-256 (64 hex chars)
    assert len(key_hash) == 64
    assert all(c in "0123456789abcdef" for c in key_hash)

    # Verify hash is correct
    expected_hash = hashlib.sha256(full_key.encode()).hexdigest()
    assert key_hash == expected_hash


def test_generate_key_uniqueness():
    """Test that generated keys are unique."""
    keys = [APIKeyAuth.generate_key()[0] for _ in range(100)]
    assert len(keys) == len(set(keys))  # All keys should be unique


def test_hash_key():
    """Test key hashing function."""
    test_key = "sk_live_test123"
    expected_hash = hashlib.sha256(test_key.encode()).hexdigest()

    hashed = APIKeyAuth.hash_key(test_key)

    assert hashed == expected_hash
    assert len(hashed) == 64


# ============================================================================
# Test: Create API Key
# ============================================================================


def test_create_api_key_success(db_session, test_user_id):
    """Test successful API key creation."""
    request = APIKeyCreateRequest(
        key_name="Test API Key",
        rate_limit_requests=1000,
    )

    response = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Check response structure
    assert response.key_name == "Test API Key"
    assert response.api_key.startswith("sk_live_")
    assert len(response.api_key) > 40
    assert response.rate_limit_requests == 1000
    assert response.created_at is not None

    # Verify key is in database (hashed, not plaintext)
    db_key = db_session.query(APIKeyORM).filter_by(id=response.id).first()
    assert db_key is not None
    assert db_key.key_hash != response.api_key  # Should be hashed
    assert len(db_key.key_hash) == 64  # SHA-256 hash length

    # Verify hash is correct
    expected_hash = hashlib.sha256(response.api_key.encode()).hexdigest()
    assert db_key.key_hash == expected_hash


def test_create_api_key_with_expiration(db_session, test_user_id):
    """Test API key creation with expiration."""
    request = APIKeyCreateRequest(
        key_name="Expiring Key",
        expires_in_days=30,
        rate_limit_requests=500,
    )

    response = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    assert response.expires_at is not None
    expected_expiry = datetime.utcnow() + timedelta(days=30)
    # Allow 1 minute tolerance for test execution time
    assert abs((response.expires_at - expected_expiry).total_seconds()) < 60


def test_create_api_key_duplicate_name(db_session, test_user_id):
    """Test that duplicate key names are rejected."""
    request = APIKeyCreateRequest(key_name="Duplicate Key")

    # Create first key
    APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Try to create second key with same name
    with pytest.raises(HTTPException) as exc:
        APIKeyAuth.create_api_key(db_session, test_user_id, request)

    assert exc.value.status_code == 409
    assert "already exists" in exc.value.detail.lower()


# ============================================================================
# Test: Validate API Key
# ============================================================================


def test_validate_key_success(db_session, test_user_id):
    """Test successful API key validation."""
    # Create a key
    request = APIKeyCreateRequest(key_name="Valid Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Validate the key
    user_id, api_key_orm = APIKeyAuth.validate_key(
        db_session, created.api_key, check_rate_limit=False
    )

    assert user_id == test_user_id
    assert api_key_orm.key_name == "Valid Key"
    assert api_key_orm.is_active is True
    assert api_key_orm.is_revoked is False


def test_validate_key_invalid(db_session):
    """Test validation of invalid API key."""
    invalid_key = "sk_live_invalid_key_12345"

    with pytest.raises(HTTPException) as exc:
        APIKeyAuth.validate_key(db_session, invalid_key, check_rate_limit=False)

    assert exc.value.status_code == 401
    assert "Invalid API key" in exc.value.detail


def test_validate_key_revoked(db_session, test_user_id):
    """Test validation of revoked API key."""
    # Create and revoke a key
    request = APIKeyCreateRequest(key_name="Revoked Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Revoke it
    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()
    db_key.is_revoked = True
    db_session.commit()

    # Try to validate
    with pytest.raises(HTTPException) as exc:
        APIKeyAuth.validate_key(db_session, created.api_key, check_rate_limit=False)

    assert exc.value.status_code == 401
    assert "revoked" in exc.value.detail.lower()


def test_validate_key_expired(db_session, test_user_id):
    """Test validation of expired API key."""
    # Create key that expired yesterday
    request = APIKeyCreateRequest(key_name="Expired Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Set expiration to yesterday
    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()
    db_key.expires_at = datetime.utcnow() - timedelta(days=1)
    db_session.commit()

    # Try to validate
    with pytest.raises(HTTPException) as exc:
        APIKeyAuth.validate_key(db_session, created.api_key, check_rate_limit=False)

    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


# ============================================================================
# Test: Rate Limiting
# ============================================================================


def test_rate_limiting_enforcement(db_session, test_user_id):
    """Test that rate limiting is enforced (1000 req/hour)."""
    # Create key with low rate limit for testing
    request = APIKeyCreateRequest(key_name="Rate Limited Key", rate_limit_requests=5)
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Make requests up to the limit
    for i in range(5):
        user_id, _ = APIKeyAuth.validate_key(
            db_session, created.api_key, check_rate_limit=True
        )
        assert user_id == test_user_id

    # Next request should fail with 429
    with pytest.raises(HTTPException) as exc:
        APIKeyAuth.validate_key(db_session, created.api_key, check_rate_limit=True)

    assert exc.value.status_code == 429
    assert "Rate limit exceeded" in exc.value.detail


def test_rate_limiting_window_reset(db_session, test_user_id):
    """Test that rate limit window resets correctly."""
    request = APIKeyCreateRequest(key_name="Window Reset Key", rate_limit_requests=5)
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Use up the limit
    for _ in range(5):
        APIKeyAuth.validate_key(db_session, created.api_key, check_rate_limit=True)

    # Manually reset the window (simulate time passing)
    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()
    db_key.rate_limit_window_start = datetime.utcnow() - timedelta(hours=2)
    db_session.commit()

    # Should be able to make requests again
    user_id, _ = APIKeyAuth.validate_key(
        db_session, created.api_key, check_rate_limit=True
    )
    assert user_id == test_user_id


# ============================================================================
# Test: List API Keys
# ============================================================================


def test_list_keys_empty(db_session, test_user_id):
    """Test listing keys when user has none."""
    response = APIKeyAuth.list_keys(db_session, test_user_id)

    assert response.total == 0
    assert len(response.keys) == 0


def test_list_keys_multiple(db_session, test_user_id):
    """Test listing multiple API keys."""
    # Create 3 keys
    for i in range(3):
        request = APIKeyCreateRequest(key_name=f"Key {i}")
        APIKeyAuth.create_api_key(db_session, test_user_id, request)

    response = APIKeyAuth.list_keys(db_session, test_user_id)

    assert response.total == 3
    assert len(response.keys) == 3

    # Check keys are ordered by created_at desc
    created_times = [key.created_at for key in response.keys]
    assert created_times == sorted(created_times, reverse=True)


def test_list_keys_exclude_revoked(db_session, test_user_id):
    """Test that revoked keys are excluded by default."""
    # Create 2 keys
    request1 = APIKeyCreateRequest(key_name="Active Key")
    request2 = APIKeyCreateRequest(key_name="Revoked Key")

    created1 = APIKeyAuth.create_api_key(db_session, test_user_id, request1)
    created2 = APIKeyAuth.create_api_key(db_session, test_user_id, request2)

    # Revoke one
    APIKeyAuth.revoke_key(db_session, test_user_id, created2.id)

    # List without revoked
    response = APIKeyAuth.list_keys(db_session, test_user_id, include_revoked=False)
    assert response.total == 1
    assert response.keys[0].key_name == "Active Key"

    # List with revoked
    response_all = APIKeyAuth.list_keys(db_session, test_user_id, include_revoked=True)
    assert response_all.total == 2


# ============================================================================
# Test: Revoke API Key
# ============================================================================


def test_revoke_key_success(db_session, test_user_id):
    """Test successful key revocation."""
    request = APIKeyCreateRequest(key_name="To Be Revoked")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Revoke the key
    result = APIKeyAuth.revoke_key(db_session, test_user_id, created.id)
    assert result is True

    # Verify it's revoked in database
    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()
    assert db_key.is_revoked is True
    assert db_key.revoked_at is not None


def test_revoke_key_not_found(db_session, test_user_id):
    """Test revoking non-existent key."""
    fake_id = uuid4()
    result = APIKeyAuth.revoke_key(db_session, test_user_id, fake_id)
    assert result is False


def test_revoke_key_wrong_user(db_session, test_user_id):
    """Test that users can't revoke other users' keys."""
    # Create key for test_user_id
    request = APIKeyCreateRequest(key_name="Other User Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Try to revoke with different user_id
    different_user_id = uuid4()

    with pytest.raises(HTTPException) as exc:
        APIKeyAuth.revoke_key(db_session, different_user_id, created.id)

    assert exc.value.status_code == 403


# ============================================================================
# Test: Usage Tracking
# ============================================================================


def test_usage_tracking(db_session, test_user_id):
    """Test that usage statistics are tracked correctly."""
    request = APIKeyCreateRequest(key_name="Usage Tracking Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Make 10 requests
    for _ in range(10):
        APIKeyAuth.validate_key(db_session, created.api_key, check_rate_limit=True)

    # Check usage stats
    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()
    assert db_key.request_count == 10
    assert db_key.current_usage_count == 10
    assert db_key.last_used_at is not None


# ============================================================================
# Test: Security
# ============================================================================


def test_plaintext_key_never_stored(db_session, test_user_id):
    """Test that plaintext keys are never stored in database."""
    request = APIKeyCreateRequest(key_name="Security Test Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    # Query all data from api_keys table
    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()

    # Check that plaintext key doesn't appear anywhere
    assert created.api_key not in str(db_key.key_hash)
    assert created.api_key not in str(db_key.metadata)

    # Verify only hash is stored
    assert db_key.key_hash == hashlib.sha256(created.api_key.encode()).hexdigest()


def test_hash_algorithm_sha256(db_session, test_user_id):
    """Test that SHA-256 is used for hashing."""
    request = APIKeyCreateRequest(key_name="Hash Test Key")
    created = APIKeyAuth.create_api_key(db_session, test_user_id, request)

    db_key = db_session.query(APIKeyORM).filter_by(id=created.id).first()

    # SHA-256 produces 64 hex characters
    assert len(db_key.key_hash) == 64
    assert all(c in "0123456789abcdef" for c in db_key.key_hash)

    # Verify it matches SHA-256 of the key
    expected = hashlib.sha256(created.api_key.encode()).hexdigest()
    assert db_key.key_hash == expected
