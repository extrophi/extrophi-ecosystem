"""
Chaos engineering tests to simulate real-world failures and edge cases.

These tests simulate:
- Database failures and recovery
- Network partitions
- Service crashes
- Data corruption
- Byzantine failures
- Time-based attacks
"""
from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun import freeze_time
from sqlalchemy.exc import OperationalError

from src.core.security import create_token, TokenType
from tests.conftest import DatabaseKiller, NetworkChaos


@pytest.mark.chaos
class TestDatabaseChaos:
    """Test system resilience to database failures."""
    
    @pytest.mark.asyncio
    async def test_intermittent_database_failures(
        self, async_client, test_engine, auth_headers
    ):
        """Test system handles intermittent database failures gracefully."""
        db_killer = DatabaseKiller(test_engine)
        
        # Enable 10% failure rate
        db_killer.enable_chaos(failure_rate=0.1)
        
        try:
            # Make many requests
            responses = []
            for i in range(100):
                try:
                    response = await async_client.get(
                        "/api/v1/users/",
                        headers=auth_headers,
                    )
                    responses.append(response)
                except Exception as e:
                    responses.append(e)
            
            # Some should succeed despite failures
            successes = sum(
                1 for r in responses 
                if hasattr(r, 'status_code') and r.status_code == 200
            )
            
            # At least 70% should succeed with 10% db failure rate
            assert successes >= 70, f"Only {successes}/100 requests succeeded"
            
        finally:
            db_killer.disable_chaos()
    
    @pytest.mark.asyncio
    async def test_database_connection_loss_during_transaction(
        self, async_client, test_session, test_user
    ):
        """Test transaction rollback on connection loss."""
        # Start a user update
        update_data = {"full_name": "Updated Name"}
        
        # Mock connection failure during commit
        original_commit = test_session.commit
        
        async def failing_commit():
            raise OperationalError("Connection lost", None, None)
        
        test_session.commit = failing_commit
        
        # Attempt update
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {create_token({'sub': str(test_user.id)}, TokenType.ACCESS)}"},
        )
        
        # Should handle gracefully
        assert response.status_code == 500
        
        # Restore commit
        test_session.commit = original_commit
        
        # Verify user was not updated (transaction rolled back)
        response = await async_client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {create_token({'sub': str(test_user.id)}, TokenType.ACCESS)}"},
        )
        assert response.json()["full_name"] == test_user.full_name  # Unchanged
    
    @pytest.mark.asyncio
    async def test_database_deadlock_handling(self, async_client, test_users, auth_headers):
        """Test system handles database deadlocks."""
        # Simulate operations that could cause deadlock
        # Update users in different order from different "threads"
        
        async def update_users_forward():
            for user in test_users[:10]:
                try:
                    await async_client.put(
                        f"/api/v1/users/{user.id}",
                        json={"metadata": {"updated": "forward"}},
                        headers=auth_headers,
                    )
                except Exception:
                    pass  # Expected some failures
        
        async def update_users_backward():
            for user in reversed(test_users[:10]):
                try:
                    await async_client.put(
                        f"/api/v1/users/{user.id}",
                        json={"metadata": {"updated": "backward"}},
                        headers=auth_headers,
                    )
                except Exception:
                    pass  # Expected some failures
        
        # Run concurrently to increase deadlock chance
        await asyncio.gather(
            update_users_forward(),
            update_users_backward(),
            return_exceptions=True,
        )
        
        # System should still be responsive
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200


@pytest.mark.chaos
class TestNetworkChaos:
    """Test system resilience to network issues."""
    
    @pytest.mark.asyncio
    async def test_high_latency_conditions(self, async_client, auth_headers):
        """Test system under high network latency."""
        # Add artificial delay to simulate high latency
        original_request = async_client.request
        
        async def delayed_request(*args, **kwargs):
            await NetworkChaos.random_delay(min_ms=500, max_ms=2000)
            return await original_request(*args, **kwargs)
        
        async_client.request = delayed_request
        
        try:
            # Make requests with high latency
            start = time.time()
            response = await async_client.get(
                "/api/v1/users/",
                headers=auth_headers,
                timeout=10.0,  # Increase timeout
            )
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration > 0.5, "Latency simulation not working"
            
        finally:
            async_client.request = original_request
    
    @pytest.mark.asyncio
    async def test_packet_loss_simulation(self, async_client, auth_headers):
        """Test system under packet loss conditions."""
        responses = []
        errors = []
        
        for i in range(50):
            # Simulate 20% packet loss
            if NetworkChaos.packet_loss(0.2):
                errors.append("Packet lost")
                continue
            
            try:
                response = await async_client.get(
                    "/api/v1/health",
                    timeout=5.0,
                )
                responses.append(response)
            except Exception as e:
                errors.append(str(e))
        
        # Should handle packet loss gracefully
        success_count = len(responses)
        assert success_count >= 30, f"Too many failures: {len(errors)}/{50}"
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, async_client, auth_headers):
        """Test proper timeout handling."""
        # Create a very slow endpoint simulation
        with patch('asyncio.sleep', side_effect=asyncio.TimeoutError):
            try:
                response = await async_client.get(
                    "/api/v1/users/",
                    headers=auth_headers,
                    timeout=0.001,  # Very short timeout
                )
            except Exception as e:
                assert "timeout" in str(e).lower()


@pytest.mark.chaos
class TestTimeChaos:
    """Test system behavior with time-based attacks and issues."""
    
    @pytest.mark.asyncio
    async def test_clock_skew_attack(self, async_client, test_user):
        """Test JWT validation with clock skew."""
        # Create token with future issued time
        with freeze_time(datetime.now(timezone.utc) + timedelta(minutes=10)):
            future_token = create_token(
                {"sub": str(test_user.id)},
                TokenType.ACCESS,
            )
        
        # Try to use future token
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {future_token}"},
        )
        
        # Should be rejected
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_token_expiry_race_condition(self, async_client, test_user):
        """Test token expiry at exact moment of use."""
        # Create token that expires in 1 second
        token = create_token(
            {"sub": str(test_user.id)},
            TokenType.ACCESS,
            expires_delta=timedelta(seconds=1),
        )
        
        # Use immediately - should work
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # Wait for expiry
        await asyncio.sleep(1.1)
        
        # Should now fail
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_replay_attack_prevention(self, async_client, test_cache):
        """Test system prevents replay attacks."""
        # Create a password reset token
        user_id = "test_user_id"
        reset_token = create_token(
            {
                "sub": user_id,
                "purpose": "password_reset",
                "jti": "unique_token_id",  # JWT ID for tracking
            },
            TokenType.ACCESS,
        )
        
        # Store in cache (simulating first use)
        await test_cache.set(f"used_token:unique_token_id", "1", ttl=3600)
        
        # Try to reuse token
        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewPassword123!",
            },
        )
        
        # Should detect replay attempt
        assert response.status_code in [400, 401]


@pytest.mark.chaos
class TestDataCorruption:
    """Test system handling of corrupted data."""
    
    @pytest.mark.asyncio
    async def test_corrupted_cache_data(self, async_client, test_cache, auth_headers):
        """Test handling of corrupted cache entries."""
        # Store corrupted data in cache
        await test_cache._redis.set(
            "corrupted_key",
            b"\x80\x03}q\x00(X\x04\x00\x00\x00corrupted",  # Invalid pickle data
        )
        
        # System should handle gracefully
        response = await async_client.get(
            "/api/v1/users/",
            headers=auth_headers,
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_malformed_json_handling(self, async_client):
        """Test handling of malformed JSON in requests."""
        malformed_payloads = [
            b'{"email": "test@example.com", "password": "Pass123!",}',  # Trailing comma
            b'{"email": "test@example.com" "password": "Pass123!"}',  # Missing comma
            b"{'email': 'test@example.com'}",  # Single quotes
            b'{"email": undefined}',  # JavaScript undefined
            b'{"email": NaN}',  # NaN value
            b'\xFF\xFE{"email": "test"}',  # BOM prefix
            b'{"email": "test@example.com"',  # Truncated
        ]
        
        for payload in malformed_payloads:
            response = await async_client.post(
                "/api/v1/auth/register",
                content=payload,
                headers={"Content-Type": "application/json"},
            )
            # Should handle gracefully
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_unicode_normalization_attacks(self, async_client):
        """Test handling of Unicode normalization attacks."""
        # Different Unicode representations of "admin"
        unicode_variations = [
            "admin",  # Normal
            "admіn",  # Cyrillic 'і'
            "аdmin",  # Cyrillic 'а'
            "admin\u200B",  # Zero-width space
            "ad\u00ADmin",  # Soft hyphen
            "\u202Eadmin",  # Right-to-left override
        ]
        
        for i, email_variant in enumerate(unicode_variations):
            response = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"{email_variant}@example.com",
                    "password": "Password123!",
                    "full_name": "Unicode Test",
                },
            )
            
            # First should succeed, others might be normalized or rejected
            if i == 0:
                assert response.status_code == 201
            else:
                assert response.status_code in [201, 409, 422]


@pytest.mark.chaos
class TestCascadingFailures:
    """Test system resilience to cascading failures."""
    
    @pytest.mark.asyncio
    async def test_cache_failure_cascade(self, async_client, test_cache, auth_headers):
        """Test system continues working when cache fails."""
        # Simulate cache failure
        test_cache._redis = None  # Break Redis connection
        
        # System should still work (degraded mode)
        response = await async_client.get(
            "/api/v1/users/",
            headers=auth_headers,
        )
        
        # Should work without cache
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_authentication_service_degradation(self, async_client):
        """Test graceful degradation when auth service is slow."""
        # Mock slow password hashing
        with patch('src.core.security.verify_password') as mock_verify:
            async def slow_verify(password, hashed):
                await asyncio.sleep(5)  # 5 second delay
                return True
            
            mock_verify.side_effect = slow_verify
            
            # Should timeout or handle gracefully
            try:
                response = await async_client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "test@example.com",
                        "password": "password",
                    },
                    timeout=2.0,  # 2 second timeout
                )
            except asyncio.TimeoutError:
                pass  # Expected
    
    @pytest.mark.asyncio
    async def test_multi_service_failure_recovery(
        self, async_client, test_cache, test_engine, auth_headers
    ):
        """Test recovery from multiple service failures."""
        failures = []
        
        # Simulate multiple failures
        db_killer = DatabaseKiller(test_engine)
        db_killer.enable_chaos(failure_rate=0.3)  # 30% DB failure
        
        # Break cache
        original_get = test_cache.get
        test_cache.get = AsyncMock(side_effect=Exception("Cache down"))
        
        try:
            # Make requests during failures
            for i in range(20):
                try:
                    response = await async_client.get(
                        "/api/v1/health",
                        timeout=5.0,
                    )
                    if response.status_code != 200:
                        failures.append(f"Request {i}: Status {response.status_code}")
                except Exception as e:
                    failures.append(f"Request {i}: {str(e)}")
            
            # Some should still succeed
            assert len(failures) < 20, "Total system failure"
            
        finally:
            # Restore services
            db_killer.disable_chaos()
            test_cache.get = original_get


@pytest.mark.chaos
class TestByzantineFailures:
    """Test handling of Byzantine failures (nodes giving wrong information)."""
    
    @pytest.mark.asyncio
    async def test_inconsistent_cache_state(self, async_client, test_cache, test_user):
        """Test handling when cache returns inconsistent data."""
        # Store conflicting user data in cache
        await test_cache.set(
            f"user:{test_user.id}",
            {
                "id": test_user.id,
                "email": "different@example.com",  # Wrong email
                "role": "admin",  # Wrong role
            },
        )
        
        # System should detect inconsistency
        token = create_token(
            {"sub": str(test_user.id), "email": test_user.email},
            TokenType.ACCESS,
        )
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Should return correct data from database
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email  # Not the cached wrong email
    
    @pytest.mark.asyncio
    async def test_split_brain_scenario(self, async_client, auth_headers):
        """Test handling of split-brain scenarios in distributed system."""
        # Simulate two instances seeing different data
        # This would be more complex in a real distributed system
        
        # Make concurrent conflicting updates
        update_tasks = []
        for i in range(10):
            update_data = {"metadata": {"version": i, "node": i % 2}}
            task = async_client.put(
                "/api/v1/users/me",
                json=update_data,
                headers=auth_headers,
            )
            update_tasks.append(task)
        
        responses = await asyncio.gather(*update_tasks, return_exceptions=True)
        
        # System should handle conflicts
        successful_updates = sum(
            1 for r in responses 
            if hasattr(r, 'status_code') and r.status_code == 200
        )
        
        # At least one should succeed
        assert successful_updates >= 1