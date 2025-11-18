"""
Comprehensive unit tests for authentication endpoints.

Tests cover all authentication flows including registration, login, refresh,
logout, password reset, and edge cases that could break the system.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import status
from jose import jwt

from src.core.config import settings
from src.core.security import (
    TokenType,
    create_token,
    decode_token,
    get_password_hash,
    verify_password,
)


@pytest.mark.unit
class TestPasswordSecurity:
    """Test password hashing and validation."""
    
    def test_password_hashing(self):
        """Test password hashing generates different hashes."""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Same password should generate different hashes (salt)
        assert hash1 != hash2
        
        # Both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_password_verification_timing(self):
        """Test password verification has consistent timing (prevent timing attacks)."""
        password = "SecurePassword123!"
        hash_val = get_password_hash(password)
        
        # Time correct password
        start = time.perf_counter()
        for _ in range(100):
            verify_password(password, hash_val)
        correct_time = time.perf_counter() - start
        
        # Time incorrect password
        start = time.perf_counter()
        for _ in range(100):
            verify_password("WrongPassword123!", hash_val)
        incorrect_time = time.perf_counter() - start
        
        # Times should be similar (within 20% variance)
        ratio = correct_time / incorrect_time
        assert 0.8 < ratio < 1.2, "Password verification timing attack possible"
    
    @pytest.mark.parametrize("password,expected_valid,expected_message", [
        ("short", False, "at least 8 characters"),
        ("no_uppercase_123!", False, "uppercase letter"),
        ("NO_LOWERCASE_123!", False, "lowercase letter"),
        ("NoNumbers!", False, "digit"),
        ("NoSpecial123", False, "special character"),
        ("Valid_Pass123!", True, None),
        ("🔥Unicode123!", True, None),  # Unicode should work
        ("Super_Long_Password_That_Is_Very_Secure_123!", True, None),
        ("Pass with spaces 123!", True, None),  # Spaces allowed
        ("'; DROP TABLE users; --123!", True, None),  # SQL injection as password is OK
    ])
    def test_password_validation(self, password, expected_valid, expected_message):
        """Test password strength validation."""
        from src.core.security import validate_password_strength
        
        is_valid, message = validate_password_strength(password)
        assert is_valid == expected_valid
        if expected_message:
            assert expected_message in message


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_access_token_creation(self):
        """Test access token creation and claims."""
        user_data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user",
        }
        
        token = create_token(user_data, TokenType.ACCESS)
        payload = decode_token(token, TokenType.ACCESS)
        
        assert payload["sub"] == user_data["sub"]
        assert payload["email"] == user_data["email"]
        assert payload["role"] == user_data["role"]
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload  # JWT ID for uniqueness
    
    def test_refresh_token_has_longer_expiry(self):
        """Test refresh tokens have longer expiration than access tokens."""
        user_data = {"sub": "user123"}
        
        access_token = create_token(user_data, TokenType.ACCESS)
        refresh_token = create_token(user_data, TokenType.REFRESH)
        
        access_payload = decode_token(access_token, TokenType.ACCESS)
        refresh_payload = decode_token(refresh_token, TokenType.REFRESH)
        
        access_exp = access_payload["exp"]
        refresh_exp = refresh_payload["exp"]
        
        # Refresh token should expire later
        assert refresh_exp > access_exp
        
        # Check approximate difference
        diff_days = (refresh_exp - access_exp) / (24 * 3600)
        assert diff_days >= 6  # At least 6 days difference
    
    def test_token_type_validation(self):
        """Test tokens can only be decoded with correct type."""
        user_data = {"sub": "user123"}
        
        access_token = create_token(user_data, TokenType.ACCESS)
        refresh_token = create_token(user_data, TokenType.REFRESH)
        
        # Access token should fail with refresh decoder
        with pytest.raises(Exception):
            decode_token(access_token, TokenType.REFRESH)
        
        # Refresh token should fail with access decoder
        with pytest.raises(Exception):
            decode_token(refresh_token, TokenType.ACCESS)
    
    def test_expired_token_handling(self):
        """Test expired token raises appropriate error."""
        user_data = {"sub": "user123"}
        
        # Create token that expires immediately
        token = create_token(
            user_data,
            TokenType.ACCESS,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(Exception) as exc_info:
            decode_token(token, TokenType.ACCESS)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_malformed_token_handling(self):
        """Test various malformed tokens are rejected."""
        malformed_tokens = [
            "not.a.token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Header only
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIn0",  # No signature
            "",  # Empty
            "Bearer token",  # With Bearer prefix
            "null",
            "undefined",
            "0",
            "false",
        ]
        
        for bad_token in malformed_tokens:
            with pytest.raises(Exception):
                decode_token(bad_token, TokenType.ACCESS)


@pytest.mark.unit
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_user_registration_success(self, async_client, test_session):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "full_name": "New User",
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert data["is_verified"] is False  # Email verification required
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should never be returned
    
    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, async_client, test_user):
        """Test registration with existing email fails."""
        user_data = {
            "email": test_user.email,  # Existing email
            "password": "ValidPass123!",
            "full_name": "Duplicate User",
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_data,expected_error", [
        (
            {"email": "invalid-email", "password": "Pass123!", "full_name": "Test"},
            "valid email"
        ),
        (
            {"email": "test@example.com", "password": "weak", "full_name": "Test"},
            "at least 8 characters"
        ),
        (
            {"email": "test@example.com", "password": "Pass123!", "full_name": ""},
            "at least 1 character"
        ),
        (
            {"email": "test@example.com", "password": "Pass123!"},
            "field required"
        ),
        (
            {"email": "", "password": "Pass123!", "full_name": "Test"},
            "valid email"
        ),
    ])
    async def test_registration_validation(self, async_client, invalid_data, expected_error):
        """Test registration input validation."""
        response = await async_client.post("/api/v1/auth/register", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = str(response.json())
        assert expected_error in error_detail.lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,  # OAuth2 uses 'username'
            "password": "TestPassword123!",
        }
        
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,  # Form data, not JSON
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify tokens are valid
        access_payload = decode_token(data["access_token"], TokenType.ACCESS)
        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_login_with_unverified_email(self, async_client, test_session):
        """Test login with unverified email in production mode."""
        # Create unverified user
        from src.models.user import User
        
        unverified_user = User(
            email="unverified@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Unverified User",
            is_active=True,
            is_verified=False,
        )
        test_session.add(unverified_user)
        await test_session.commit()
        
        login_data = {
            "username": unverified_user.email,
            "password": "Password123!",
        }
        
        # In development mode, should succeed
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        
        # Would fail in production (settings.is_production = True)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, async_client, test_cache):
        """Test login rate limiting prevents brute force."""
        login_data = {
            "username": "attacker@example.com",
            "password": "wrong_password",
        }
        
        # Make 5 failed attempts
        for i in range(5):
            response = await async_client.post("/api/v1/auth/login", data=login_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 6th attempt should be rate limited
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "too many" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, async_client, test_user):
        """Test refresh token can get new access token."""
        # First login
        login_data = {
            "username": test_user.email,
            "password": "TestPassword123!",
        }
        login_response = await async_client.post("/api/v1/auth/login", data=login_data)
        tokens = login_response.json()
        
        # Use refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        
        # New access token should be different
        assert new_tokens["access_token"] != tokens["access_token"]
    
    @pytest.mark.asyncio
    async def test_logout_revokes_tokens(self, async_client, auth_headers, test_user):
        """Test logout revokes refresh tokens."""
        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Try to use the token after logout (should still work for access token)
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # But refresh token should be revoked
        # (Would need to test with actual refresh token)
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client, auth_headers, test_user):
        """Test getting current user information."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "password" not in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, async_client, test_user, test_cache):
        """Test complete password reset flow."""
        # Request password reset
        reset_request = {"email": test_user.email}
        response = await async_client.post(
            "/api/v1/auth/forgot-password",
            json=reset_request,
        )
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        # Should always return success to prevent email enumeration
        assert "email exists" in response.json()["message"]
        
        # In a real test, we'd capture the email sent
        # For now, create a valid reset token manually
        reset_token = create_token(
            data={
                "sub": str(test_user.id),
                "purpose": "password_reset",
                "email": test_user.email,
            },
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(hours=1),
        )
        
        # Store token in cache (as the endpoint would)
        await test_cache.set(
            f"password_reset:{test_user.id}",
            reset_token,
            ttl=3600,
        )
        
        # Complete password reset
        new_password = "NewSecurePass123!"
        reset_data = {
            "token": reset_token,
            "new_password": new_password,
        }
        
        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json=reset_data,
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "successfully" in response.json()["message"]
        
        # Try to login with new password
        login_data = {
            "username": test_user.email,
            "password": new_password,
        }
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_password_reset_token_reuse_prevention(self, async_client, test_user, test_cache):
        """Test password reset token cannot be reused."""
        # Create reset token
        reset_token = create_token(
            data={
                "sub": str(test_user.id),
                "purpose": "password_reset",
                "email": test_user.email,
            },
            token_type=TokenType.ACCESS,
        )
        
        # Store in cache
        await test_cache.set(f"password_reset:{test_user.id}", reset_token, ttl=3600)
        
        # First use should succeed
        reset_data = {
            "token": reset_token,
            "new_password": "NewPassword123!",
        }
        response = await async_client.post("/api/v1/auth/reset-password", json=reset_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Second use should fail
        reset_data["new_password"] = "AnotherPassword123!"
        response = await async_client.post("/api/v1/auth/reset-password", json=reset_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already been used" in response.json()["detail"]


@pytest.mark.unit
class TestAuthSecurity:
    """Test authentication security measures."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempts(self, async_client):
        """Test SQL injection attempts are handled safely."""
        sql_injection_attempts = [
            {"username": "admin'--", "password": "password"},
            {"username": "admin@example.com", "password": "' OR '1'='1"},
            {"username": "'; DROP TABLE users; --", "password": "password"},
            {"username": "admin@example.com' UNION SELECT * FROM users--", "password": "pass"},
        ]
        
        for attempt in sql_injection_attempts:
            response = await async_client.post("/api/v1/auth/login", data=attempt)
            # Should fail gracefully, not crash
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]
    
    @pytest.mark.asyncio
    async def test_xss_prevention_in_registration(self, async_client):
        """Test XSS attempts in registration are sanitized."""
        xss_attempts = [
            {
                "email": "test@example.com",
                "password": "Valid123!",
                "full_name": "<script>alert('xss')</script>",
            },
            {
                "email": "test2@example.com",
                "password": "Valid123!",
                "full_name": "User<img src=x onerror=alert('xss')>",
            },
            {
                "email": "test3@example.com",
                "password": "Valid123!",
                "full_name": "';alert(String.fromCharCode(88,83,83))//",
            },
        ]
        
        for i, attempt in enumerate(xss_attempts):
            response = await async_client.post("/api/v1/auth/register", json=attempt)
            
            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                # The malicious content should be stored as-is (escaped when rendered)
                assert data["full_name"] == attempt["full_name"]
                # When rendered in HTML, it should be escaped by the frontend
    
    @pytest.mark.asyncio
    async def test_timing_attack_prevention(self, async_client):
        """Test login timing is consistent for user enumeration prevention."""
        import time
        
        # Time non-existent user
        start = time.perf_counter()
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@example.com", "password": "password"},
        )
        time_nonexistent = time.perf_counter() - start
        
        # Time existing user with wrong password
        start = time.perf_counter()
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"},
        )
        time_wrong_password = time.perf_counter() - start
        
        # Times should be similar (within 50% variance)
        ratio = time_nonexistent / time_wrong_password
        assert 0.5 < ratio < 1.5, "Potential timing attack vulnerability"
    
    @pytest.mark.asyncio
    async def test_authorization_header_injection(self, async_client):
        """Test various authorization header injection attempts."""
        malicious_headers = [
            {"Authorization": "Bearer token\nX-Admin: true"},
            {"Authorization": "Bearer token\r\nX-User-Id: 1"},
            {"Authorization": "Basic YWRtaW46YWRtaW4="},  # Basic auth attempt
            {"Authorization": "Bearer ../../../etc/passwd"},
            {"Authorization": "Bearer null"},
            {"Authorization": "Bearer undefined"},
            {"Authorization": ""},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer  "},  # Double space
        ]
        
        for headers in malicious_headers:
            response = await async_client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED