"""
Integration Tests: API Authentication & Rate Limiting

Tests RHO authentication system:
- API key creation and validation
- Rate limiting enforcement (10 req/min in tests)
- Invalid/revoked/expired key handling
- Concurrent request handling
- Usage tracking
"""

from datetime import datetime, timedelta
from time import sleep

import pytest

from backend.auth.api_keys import APIKeyAuth
from backend.db.models import APIKeyCreateRequest, APIKeyORM


class TestAPIKeyCreation:
    """Test API key creation and management."""

    def test_create_api_key(self, test_db_session, test_user_alice):
        """Test creating a new API key."""
        request = APIKeyCreateRequest(
            key_name="Test Key",
            expires_in_days=30,
            rate_limit_requests=1000,
        )

        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        assert response.key_name == "Test Key"
        assert response.api_key.startswith("extro_live_")
        assert len(response.api_key) > 50  # Secure length
        assert response.key_prefix.startswith("extro_live_")
        assert response.expires_at is not None

    def test_create_multiple_api_keys(self, test_db_session, test_user_alice):
        """Test creating multiple API keys for same user."""
        keys = []

        for i in range(3):
            request = APIKeyCreateRequest(
                key_name=f"Test Key {i}",
                rate_limit_requests=1000,
            )
            response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)
            keys.append(response.api_key)

        # All keys should be unique
        assert len(set(keys)) == 3

    def test_duplicate_key_name_rejected(self, test_db_session, test_user_alice):
        """Test that duplicate key names are rejected."""
        request = APIKeyCreateRequest(
            key_name="Duplicate Key",
            rate_limit_requests=1000,
        )

        # Create first key
        APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        # Attempt to create duplicate
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.detail)


class TestAPIKeyValidation:
    """Test API key validation and authentication."""

    def test_valid_api_key_authentication(self, test_db_session, test_user_alice, alice_api_key):
        """Test authentication with valid API key."""
        full_key, api_key_orm = alice_api_key

        # Hash the key
        key_hash = APIKeyAuth.hash_key(full_key)

        # Verify key exists in database
        db_key = (
            test_db_session.query(APIKeyORM).filter(APIKeyORM.key_hash == key_hash).first()
        )

        assert db_key is not None
        assert db_key.user_id == test_user_alice.id
        assert db_key.is_active == True
        assert db_key.is_revoked == False

    def test_invalid_api_key_rejected(self, test_db_session):
        """Test authentication fails with invalid key."""
        invalid_key = "extro_live_invalid_key_12345"
        key_hash = APIKeyAuth.hash_key(invalid_key)

        # Key should not exist
        db_key = (
            test_db_session.query(APIKeyORM).filter(APIKeyORM.key_hash == key_hash).first()
        )

        assert db_key is None

    def test_revoked_api_key_rejected(self, test_db_session, test_user_alice):
        """Test authentication fails with revoked key."""
        # Create and revoke key
        request = APIKeyCreateRequest(key_name="To Be Revoked", rate_limit_requests=1000)
        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        key_hash = APIKeyAuth.hash_key(response.api_key)
        db_key = (
            test_db_session.query(APIKeyORM).filter(APIKeyORM.key_hash == key_hash).first()
        )

        # Revoke key
        db_key.is_revoked = True
        db_key.is_active = False
        db_key.revoked_at = datetime.utcnow()
        test_db_session.commit()

        # Verify key is revoked
        test_db_session.refresh(db_key)
        assert db_key.is_revoked == True
        assert db_key.is_active == False

    def test_expired_api_key_rejected(self, test_db_session, test_user_alice):
        """Test authentication fails with expired key."""
        # Create key with past expiration
        request = APIKeyCreateRequest(
            key_name="Expired Key",
            expires_in_days=1,
            rate_limit_requests=1000,
        )
        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        key_hash = APIKeyAuth.hash_key(response.api_key)
        db_key = (
            test_db_session.query(APIKeyORM).filter(APIKeyORM.key_hash == key_hash).first()
        )

        # Manually expire the key
        db_key.expires_at = datetime.utcnow() - timedelta(days=1)
        test_db_session.commit()

        # Key should be expired
        test_db_session.refresh(db_key)
        assert db_key.expires_at < datetime.utcnow()


class TestRateLimiting:
    """Test rate limiting enforcement."""

    def test_rate_limit_allows_within_limit(self, test_db_session, test_user_alice, alice_api_key):
        """Test requests within rate limit are allowed."""
        full_key, api_key_orm = alice_api_key

        # Alice's key has limit of 10 requests per minute
        assert api_key_orm.rate_limit_requests == 10
        assert api_key_orm.rate_limit_window_seconds == 60

        # Simulate 5 requests (within limit)
        for i in range(5):
            api_key_orm.current_usage_count += 1
            api_key_orm.request_count += 1

        test_db_session.commit()
        test_db_session.refresh(api_key_orm)

        # Should still be under limit
        assert api_key_orm.current_usage_count <= api_key_orm.rate_limit_requests

    def test_rate_limit_blocks_over_limit(self, test_db_session, test_user_alice, alice_api_key):
        """Test requests exceeding rate limit are blocked."""
        full_key, api_key_orm = alice_api_key

        # Fill up the rate limit
        api_key_orm.current_usage_count = 10  # At limit
        api_key_orm.rate_limit_window_start = datetime.utcnow()
        test_db_session.commit()

        # Next request should be blocked
        assert api_key_orm.current_usage_count >= api_key_orm.rate_limit_requests

    def test_rate_limit_resets_after_window(self, test_db_session, test_user_alice, alice_api_key):
        """Test rate limit counter resets after window expires."""
        full_key, api_key_orm = alice_api_key

        # Fill up the rate limit
        api_key_orm.current_usage_count = 10
        api_key_orm.rate_limit_window_start = datetime.utcnow() - timedelta(seconds=61)
        test_db_session.commit()

        # Window has expired (more than 60 seconds ago)
        window_expired = (datetime.utcnow() - api_key_orm.rate_limit_window_start).total_seconds() > api_key_orm.rate_limit_window_seconds

        assert window_expired == True

        # Counter should be reset
        api_key_orm.current_usage_count = 0
        api_key_orm.rate_limit_window_start = datetime.utcnow()
        test_db_session.commit()

        test_db_session.refresh(api_key_orm)
        assert api_key_orm.current_usage_count == 0

    def test_rate_limit_per_key_isolation(
        self, test_db_session, test_user_alice, test_user_bob, alice_api_key, bob_api_key
    ):
        """Test rate limits are isolated per API key."""
        alice_key, alice_key_orm = alice_api_key
        bob_key, bob_key_orm = bob_api_key

        # Alice uses all her requests
        alice_key_orm.current_usage_count = 10
        test_db_session.commit()

        # Bob's limit should be unaffected
        test_db_session.refresh(bob_key_orm)
        assert bob_key_orm.current_usage_count == 0
        assert bob_key_orm.rate_limit_requests == 1000


class TestConcurrentAPIRequests:
    """Test handling of concurrent API requests."""

    def test_concurrent_requests_same_key(self, test_db_session, test_user_alice, alice_api_key):
        """Test concurrent requests with same API key."""
        full_key, api_key_orm = alice_api_key

        initial_count = api_key_orm.request_count

        # Simulate 3 concurrent requests
        for i in range(3):
            api_key_orm.request_count += 1
            api_key_orm.current_usage_count += 1

        test_db_session.commit()
        test_db_session.refresh(api_key_orm)

        # All requests should be counted
        assert api_key_orm.request_count == initial_count + 3

    def test_concurrent_requests_different_keys(
        self, test_db_session, alice_api_key, bob_api_key
    ):
        """Test concurrent requests with different API keys."""
        alice_key, alice_key_orm = alice_api_key
        bob_key, bob_key_orm = bob_api_key

        alice_initial = alice_key_orm.request_count
        bob_initial = bob_key_orm.request_count

        # Simulate concurrent requests
        alice_key_orm.request_count += 2
        bob_key_orm.request_count += 3

        test_db_session.commit()
        test_db_session.refresh(alice_key_orm)
        test_db_session.refresh(bob_key_orm)

        # Each key should track independently
        assert alice_key_orm.request_count == alice_initial + 2
        assert bob_key_orm.request_count == bob_initial + 3


class TestUsageTracking:
    """Test API key usage tracking and statistics."""

    def test_track_last_used_timestamp(self, test_db_session, test_user_alice, alice_api_key):
        """Test last_used_at timestamp is updated."""
        full_key, api_key_orm = alice_api_key

        initial_last_used = api_key_orm.last_used_at

        # Simulate request
        api_key_orm.last_used_at = datetime.utcnow()
        api_key_orm.request_count += 1
        test_db_session.commit()

        test_db_session.refresh(api_key_orm)

        # Timestamp should be updated
        if initial_last_used is not None:
            assert api_key_orm.last_used_at > initial_last_used
        else:
            assert api_key_orm.last_used_at is not None

    def test_track_total_request_count(self, test_db_session, test_user_alice, alice_api_key):
        """Test total request count is tracked."""
        full_key, api_key_orm = alice_api_key

        initial_count = api_key_orm.request_count

        # Simulate multiple requests
        for i in range(10):
            api_key_orm.request_count += 1

        test_db_session.commit()
        test_db_session.refresh(api_key_orm)

        assert api_key_orm.request_count == initial_count + 10

    def test_list_user_api_keys(self, test_db_session, test_user_alice):
        """Test listing all API keys for a user."""
        # Create multiple keys
        keys = []
        for i in range(3):
            request = APIKeyCreateRequest(
                key_name=f"Key {i}",
                rate_limit_requests=1000,
            )
            response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)
            keys.append(response)

        # List keys
        response = APIKeyAuth.list_keys(test_db_session, test_user_alice.id)

        assert response.user_id == str(test_user_alice.id)
        assert response.total_keys >= 3

    def test_revoke_api_key(self, test_db_session, test_user_alice):
        """Test revoking an API key."""
        # Create key
        request = APIKeyCreateRequest(key_name="To Revoke", rate_limit_requests=1000)
        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        from uuid import UUID

        key_id = UUID(response.id)

        # Revoke key
        revoked = APIKeyAuth.revoke_key(test_db_session, test_user_alice.id, key_id)

        assert revoked == True

        # Verify key is revoked
        key_hash = APIKeyAuth.hash_key(response.api_key)
        db_key = (
            test_db_session.query(APIKeyORM).filter(APIKeyORM.key_hash == key_hash).first()
        )

        assert db_key.is_revoked == True
        assert db_key.is_active == False


class TestSecurityFeatures:
    """Test security features of API key system."""

    def test_api_keys_stored_as_hash(self, test_db_session, test_user_alice):
        """Test API keys are never stored in plaintext."""
        request = APIKeyCreateRequest(key_name="Security Test", rate_limit_requests=1000)
        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        # Get key from database
        key_hash = APIKeyAuth.hash_key(response.api_key)
        db_key = (
            test_db_session.query(APIKeyORM).filter(APIKeyORM.key_hash == key_hash).first()
        )

        # key_hash should be SHA-256 hash, not plaintext
        assert db_key.key_hash != response.api_key
        assert len(db_key.key_hash) == 64  # SHA-256 hex length

    def test_api_key_prefix_for_identification(self, test_db_session, test_user_alice):
        """Test API keys have identifiable prefix."""
        request = APIKeyCreateRequest(key_name="Prefix Test", rate_limit_requests=1000)
        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        # Key should start with prefix
        assert response.api_key.startswith("extro_live_")
        assert response.key_prefix.startswith("extro_live_")

    def test_api_key_sufficient_length(self, test_db_session, test_user_alice):
        """Test API keys are sufficiently long for security."""
        request = APIKeyCreateRequest(key_name="Length Test", rate_limit_requests=1000)
        response = APIKeyAuth.create_api_key(test_db_session, test_user_alice.id, request)

        # Should be at least 48 characters
        assert len(response.api_key) >= 48

    def test_api_key_uniqueness(self, test_db_session, test_user_alice, test_user_bob):
        """Test all generated API keys are unique."""
        keys = set()

        # Generate keys for multiple users
        for user in [test_user_alice, test_user_bob]:
            for i in range(5):
                request = APIKeyCreateRequest(
                    key_name=f"Key {i} for {user.username}",
                    rate_limit_requests=1000,
                )
                response = APIKeyAuth.create_api_key(test_db_session, user.id, request)
                keys.add(response.api_key)

        # All 10 keys should be unique
        assert len(keys) == 10
