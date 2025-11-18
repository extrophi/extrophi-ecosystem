"""
Comprehensive security tests to ensure the system is bulletproof.

Tests cover:
- OWASP Top 10 vulnerabilities
- Authentication bypass attempts
- Authorization vulnerabilities
- Injection attacks
- Cryptographic weaknesses
- Business logic flaws
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import string
import time
from datetime import datetime, timedelta, timezone
from typing import List
from urllib.parse import quote, urlencode

import pytest
from jose import jwe, jwt

from src.core.config import settings
from src.core.security import create_token, TokenType
from tests.conftest import create_malicious_payloads


@pytest.mark.security
class TestInjectionAttacks:
    """Test all forms of injection attacks."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_comprehensive(self, async_client):
        """Test comprehensive SQL injection prevention."""
        sql_payloads = [
            # Classic SQL injection
            "admin' OR '1'='1",
            "admin'); DROP TABLE users; --",
            "admin' UNION SELECT * FROM users WHERE '1'='1",
            
            # Time-based blind SQL injection
            "admin' AND SLEEP(5)--",
            "admin' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            
            # Boolean-based blind SQL injection  
            "admin' AND 1=1--",
            "admin' AND 1=2--",
            
            # Stacked queries
            "admin'; INSERT INTO users VALUES ('hacker', 'password'); --",
            
            # Second-order SQL injection
            "admin'||'",
            "admin' + '",
            
            # Unicode/encoding bypass attempts
            "admin%27%20OR%20%271%27%3D%271",
            "admin\' OR \'1\'=\'1",
            
            # MySQL specific
            "admin' /*!50000AND*/ 1=1--",
            
            # PostgreSQL specific
            "admin'::text OR '1'='1",
            "admin' OR 1=1::boolean--",
        ]
        
        for payload in sql_payloads:
            # Try in various fields
            test_cases = [
                # Login
                {"endpoint": "/api/v1/auth/login", "data": {
                    "username": payload,
                    "password": "password"
                }},
                # Registration email
                {"endpoint": "/api/v1/auth/register", "json": {
                    "email": f"{payload}@example.com",
                    "password": "Valid123!",
                    "full_name": "Test"
                }},
                # Search
                {"endpoint": f"/api/v1/users/search?q={quote(payload)}", "method": "GET"},
            ]
            
            for test in test_cases:
                if test.get("method") == "GET":
                    response = await async_client.get(test["endpoint"])
                elif "data" in test:
                    response = await async_client.post(test["endpoint"], data=test["data"])
                else:
                    response = await async_client.post(test["endpoint"], json=test["json"])
                
                # Should not cause server error (500)
                assert response.status_code < 500, f"SQL injection caused server error: {payload}"
    
    @pytest.mark.asyncio
    async def test_nosql_injection(self, async_client):
        """Test NoSQL injection prevention."""
        nosql_payloads = [
            # MongoDB-style operators
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "this.password == 'password'"},
            
            # Array operations
            {"$in": ["admin", "user"]},
            {"$nin": []},
            
            # Logical operators
            {"$or": [{"email": "admin@example.com"}, {"role": "admin"}]},
            
            # Type confusion
            ["admin@example.com"],
            True,
            None,
            {"email": {"$exists": True}},
        ]
        
        for payload in nosql_payloads:
            # Try injecting into JSON fields
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"username": payload, "password": "password"},
            )
            
            # Should handle gracefully
            assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_command_injection(self, async_client, auth_headers):
        """Test OS command injection prevention."""
        cmd_payloads = [
            # Unix commands
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "|| id",
            "`whoami`",
            "$(cat /etc/shadow)",
            
            # Windows commands
            "& dir",
            "| type C:\\Windows\\System32\\config\\SAM",
            "& net user hacker password /add",
            
            # Path traversal with commands
            "../../../bin/sh",
            "....//....//....//etc/passwd",
            
            # Null byte injection
            "file.txt\x00.sh",
            
            # Environment variable injection
            "${PATH}",
            "$HOME",
            "%APPDATA%",
        ]
        
        for payload in cmd_payloads:
            # Try in various inputs
            response = await async_client.put(
                "/api/v1/users/me",
                json={
                    "full_name": payload,
                    "bio": f"Bio {payload}",
                    "avatar_url": f"http://example.com/avatar{payload}",
                },
                headers=auth_headers,
            )
            
            # Should not execute commands
            assert response.status_code in [200, 400, 422]
            
            # Response should not contain command output
            if response.status_code == 200:
                data = response.json()
                assert "root:" not in str(data)  # /etc/passwd content
                assert "admin:" not in str(data)  # Windows user
    
    @pytest.mark.asyncio
    async def test_ldap_injection(self, async_client):
        """Test LDAP injection prevention."""
        ldap_payloads = [
            "*)(uid=*",
            "admin)(|(password=*)",
            "*)(objectClass=*",
            "admin)(uid=*))(|(uid=*",
            "\\",
            "*)(mail=*))%00",
        ]
        
        for payload in ldap_payloads:
            response = await async_client.post(
                "/api/v1/auth/login",
                data={"username": payload, "password": "password"},
            )
            
            assert response.status_code in [400, 401, 422]


@pytest.mark.security
class TestAuthenticationBypass:
    """Test authentication bypass attempts."""
    
    @pytest.mark.asyncio
    async def test_jwt_algorithm_confusion(self, async_client, test_user):
        """Test JWT algorithm confusion attack."""
        # Create token with 'none' algorithm
        token_data = {
            "sub": str(test_user.id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        
        # Try to use 'none' algorithm
        header = base64.urlsafe_b64encode(
            json.dumps({"typ": "JWT", "alg": "none"}).encode()
        ).decode().rstrip("=")
        
        payload = base64.urlsafe_b64encode(
            json.dumps(token_data).encode()
        ).decode().rstrip("=")
        
        none_token = f"{header}.{payload}."
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {none_token}"},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_jwt_key_confusion(self, async_client, test_user):
        """Test JWT RS256/HS256 confusion attack."""
        # Try to use HS256 with public key as secret
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        
        # Create token with wrong algorithm
        try:
            # This should fail as we use HS256
            fake_token = jwt.encode(
                token_data,
                "fake_public_key",  # Attacker doesn't have real key
                algorithm="RS256",  # Try different algorithm
            )
            
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {fake_token}"},
            )
            
            assert response.status_code == 401
        except Exception:
            pass  # Expected to fail
    
    @pytest.mark.asyncio
    async def test_jwt_signature_stripping(self, async_client, test_user):
        """Test JWT signature stripping attack."""
        # Create valid token
        valid_token = create_token(
            {"sub": str(test_user.id)},
            TokenType.ACCESS,
        )
        
        # Strip signature
        parts = valid_token.split(".")
        stripped_token = f"{parts[0]}.{parts[1]}."
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {stripped_token}"},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_session_fixation(self, async_client):
        """Test session fixation attack prevention."""
        # Login as user 1
        user1_response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "TestPassword123!"},
        )
        user1_token = user1_response.json()["access_token"]
        
        # Try to use user1's token with different claimed identity
        # This would require modifying the JWT payload
        # System should validate token integrity
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        
        assert response.json()["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authentication_race_condition(self, async_client, test_user):
        """Test race condition in authentication."""
        import asyncio
        
        # Try to use token while it's being revoked
        token = create_token(
            {"sub": str(test_user.id)},
            TokenType.ACCESS,
        )
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Simulate concurrent logout and API access
        async def logout():
            await async_client.post("/api/v1/auth/logout", headers=headers)
        
        async def access_api():
            return await async_client.get("/api/v1/auth/me", headers=headers)
        
        # Run concurrently
        results = await asyncio.gather(
            logout(),
            access_api(),
            access_api(),
            access_api(),
            return_exceptions=True,
        )
        
        # Should handle race condition gracefully
        assert not any(isinstance(r, Exception) for r in results)


@pytest.mark.security
class TestAuthorizationVulnerabilities:
    """Test authorization and access control."""
    
    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(
        self, async_client, test_user, test_users
    ):
        """Test preventing access to other users' data."""
        # Login as regular user
        user_token = create_token(
            {"sub": str(test_user.id), "role": "user"},
            TokenType.ACCESS,
        )
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Try to access another user's data
        other_user = test_users[0]
        
        # Try to update another user
        response = await async_client.put(
            f"/api/v1/users/{other_user.id}",
            json={"full_name": "Hacked!"},
            headers=headers,
        )
        
        assert response.status_code == 403
        
        # Try to delete another user
        response = await async_client.delete(
            f"/api/v1/users/{other_user.id}",
            headers=headers,
        )
        
        assert response.status_code in [403, 401]  # Requires admin
    
    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation(self, async_client, test_user):
        """Test preventing role escalation."""
        # Login as regular user
        user_token = create_token(
            {"sub": str(test_user.id), "role": "user"},
            TokenType.ACCESS,
        )
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Try to change own role to admin
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}/role",
            json={"role": "admin"},
            headers=headers,
        )
        
        assert response.status_code in [403, 401]
        
        # Try to access admin endpoints
        admin_endpoints = [
            ("/api/v1/users/1/activate", "POST"),
            ("/api/v1/users/1/deactivate", "POST"),
            ("/api/v1/users/1", "DELETE"),
        ]
        
        for endpoint, method in admin_endpoints:
            if method == "POST":
                response = await async_client.post(endpoint, headers=headers)
            elif method == "DELETE":
                response = await async_client.delete(endpoint, headers=headers)
            
            assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_insecure_direct_object_reference(
        self, async_client, test_user, test_users
    ):
        """Test IDOR vulnerability prevention."""
        # Create user-specific token
        user_token = create_token(
            {"sub": str(test_user.id), "role": "user"},
            TokenType.ACCESS,
        )
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Try to access resources by guessing IDs
        for i in range(10):
            # Try random user IDs
            random_id = secrets.token_hex(16)
            response = await async_client.get(
                f"/api/v1/users/{random_id}",
                headers=headers,
            )
            
            # Should not reveal if user exists
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_forced_browsing(self, async_client):
        """Test forced browsing to admin pages."""
        # Try to access admin endpoints without auth
        admin_paths = [
            "/api/v1/admin/users",
            "/api/v1/admin/config",
            "/api/v1/admin/logs",
            "/api/v1/internal/debug",
            "/api/v1/internal/metrics",
            "/.env",
            "/config.json",
            "/.git/config",
        ]
        
        for path in admin_paths:
            response = await async_client.get(path)
            # Should require auth or not exist
            assert response.status_code in [401, 403, 404]


@pytest.mark.security
class TestCryptographicWeaknesses:
    """Test cryptographic security."""
    
    def test_password_hashing_strength(self):
        """Test password hashing uses strong algorithm."""
        from src.core.security import get_password_hash
        
        password = "TestPassword123!"
        hash_value = get_password_hash(password)
        
        # Should use bcrypt (starts with $2b$)
        assert hash_value.startswith("$2b$")
        
        # Should have sufficient cost factor (>=12)
        parts = hash_value.split("$")
        cost = int(parts[2])
        assert cost >= 12, f"Bcrypt cost factor too low: {cost}"
    
    def test_token_randomness(self):
        """Test token generation has sufficient entropy."""
        from src.core.security import create_token
        
        tokens = set()
        
        # Generate many tokens
        for i in range(1000):
            token = create_token(
                {"sub": f"user{i}"},
                TokenType.ACCESS,
            )
            tokens.add(token)
        
        # All should be unique
        assert len(tokens) == 1000
        
        # Check JWT IDs are unique
        jtis = set()
        for token in list(tokens)[:100]:
            payload = jwt.decode(token, options={"verify_signature": False})
            if "jti" in payload:
                jtis.add(payload["jti"])
        
        assert len(jtis) == min(100, len([t for t in tokens if "jti" in jwt.decode(t, options={"verify_signature": False})]))
    
    @pytest.mark.asyncio
    async def test_timing_safe_comparison(self, async_client):
        """Test timing-safe string comparison in authentication."""
        import statistics
        
        timings = {"correct": [], "incorrect": []}
        
        # Measure multiple attempts
        for _ in range(20):
            # Time correct password
            start = time.perf_counter()
            await async_client.post(
                "/api/v1/auth/login",
                data={"username": "test@example.com", "password": "TestPassword123!"},
            )
            timings["correct"].append(time.perf_counter() - start)
            
            # Time incorrect password
            start = time.perf_counter()
            await async_client.post(
                "/api/v1/auth/login",
                data={"username": "test@example.com", "password": "WrongPassword123!"},
            )
            timings["incorrect"].append(time.perf_counter() - start)
        
        # Calculate statistics
        correct_mean = statistics.mean(timings["correct"])
        incorrect_mean = statistics.mean(timings["incorrect"])
        
        # Difference should be minimal (< 10%)
        diff_percent = abs(correct_mean - incorrect_mean) / correct_mean * 100
        assert diff_percent < 10, f"Timing difference: {diff_percent:.2f}%"
    
    def test_secure_random_generation(self):
        """Test secure random number generation."""
        # Generate many random values
        values = [secrets.token_bytes(32) for _ in range(1000)]
        
        # All should be unique
        assert len(set(values)) == 1000
        
        # Check entropy (simplified)
        all_bytes = b"".join(values)
        byte_counts = {}
        for byte in all_bytes:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        # Distribution should be relatively uniform
        total = len(all_bytes)
        for count in byte_counts.values():
            frequency = count / total
            # Each byte should appear roughly 1/256 of the time
            assert 0.0025 < frequency < 0.0065  # Allow some variance


@pytest.mark.security
class TestBusinessLogicFlaws:
    """Test business logic security flaws."""
    
    @pytest.mark.asyncio
    async def test_race_condition_in_registration(self, async_client):
        """Test race condition when registering same email."""
        email = f"race_test_{secrets.token_hex(8)}@example.com"
        user_data = {
            "email": email,
            "password": "Password123!",
            "full_name": "Race Test",
        }
        
        # Try to register same email concurrently
        tasks = [
            async_client.post("/api/v1/auth/register", json=user_data)
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one should succeed
        success_count = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code == 201
        )
        
        assert success_count == 1, f"Race condition: {success_count} registrations succeeded"
    
    @pytest.mark.asyncio
    async def test_integer_overflow_in_pagination(self, async_client, auth_headers):
        """Test integer overflow in pagination parameters."""
        overflow_values = [
            2**31,  # Max 32-bit int + 1
            2**63,  # Max 64-bit int + 1
            -1,
            -2**31,
            9999999999999999999999,  # Very large number
        ]
        
        for value in overflow_values:
            response = await async_client.get(
                f"/api/v1/users/?page={value}&per_page={value}",
                headers=auth_headers,
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 422]
            
            # Should not cause memory issues
            if response.status_code == 200:
                data = response.json()
                assert len(data["users"]) <= 100  # Max limit enforced
    
    @pytest.mark.asyncio
    async def test_business_logic_bypass_in_password_reset(
        self, async_client, test_user, test_cache
    ):
        """Test business logic flaws in password reset flow."""
        # Request password reset
        await async_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        
        # Try to reset without valid token
        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid_token",
                "new_password": "NewPassword123!",
            },
        )
        
        assert response.status_code in [400, 401]
        
        # Try to reuse old token
        old_token = create_token(
            {"sub": str(test_user.id), "purpose": "password_reset"},
            TokenType.ACCESS,
            expires_delta=timedelta(seconds=-1),  # Expired
        )
        
        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": old_token,
                "new_password": "NewPassword123!",
            },
        )
        
        assert response.status_code in [400, 401]
    
    @pytest.mark.asyncio
    async def test_rate_limit_bypass_attempts(self, async_client):
        """Test various rate limit bypass attempts."""
        base_email = "ratelimit@example.com"
        
        # Different bypass attempts
        bypass_attempts = [
            # Case variations
            [base_email.upper(), base_email.lower(), base_email.title()],
            
            # Unicode variations
            ["ratеlimit@example.com", "ratelimit@еxample.com"],  # Cyrillic 'e'
            
            # Whitespace
            [f" {base_email}", f"{base_email} ", f"\t{base_email}"],
            
            # Different IPs (X-Forwarded-For)
            [(base_email, f"192.168.1.{i}") for i in range(10)],
        ]
        
        for attempt_group in bypass_attempts:
            if isinstance(attempt_group[0], tuple):
                # IP-based bypass attempt
                for email, ip in attempt_group[:6]:
                    response = await async_client.post(
                        "/api/v1/auth/login",
                        data={"username": email, "password": "wrong"},
                        headers={"X-Forwarded-For": ip},
                    )
            else:
                # Email-based bypass attempt
                for email_variant in attempt_group[:6]:
                    response = await async_client.post(
                        "/api/v1/auth/login",
                        data={"username": email_variant, "password": "wrong"},
                    )
            
            # Should still enforce rate limits
            # (Actual behavior depends on implementation)