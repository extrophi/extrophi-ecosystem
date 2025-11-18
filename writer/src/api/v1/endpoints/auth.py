"""
Authentication endpoints for user registration, login, and token management.

This module implements JWT-based authentication with refresh tokens,
user registration with email verification, and secure password handling
following OWASP best practices.

Endpoints:
    POST /register - User registration with email verification
    POST /login - User authentication with JWT tokens
    POST /refresh - Refresh access token using refresh token
    POST /logout - Revoke tokens and clear session
    GET /me - Get current authenticated user details
    POST /forgot-password - Initiate password reset flow
    POST /reset-password - Complete password reset
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache_manager
from src.core.config import settings
from src.core.database import get_session
from src.core.security import (
    TokenType,
    create_token,
    decode_token,
    get_current_active_user,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from src.models.user import User, UserCreate as UserCreateSchema

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


# Pydantic schemas for request/response
class RegisterRequest(BaseModel):
    """User registration request schema."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="user@example.com",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password (min 8 characters)",
        example="SecurePass123!",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name",
        example="John Doe",
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


class TokenResponse(BaseModel):
    """JWT token response schema."""
    
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
    )


class UserResponse(BaseModel):
    """User response schema (public data only)."""
    
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Password reset initiation request."""
    
    email: EmailStr = Field(
        ...,
        description="Email address associated with the account",
    )


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation request."""
    
    token: str = Field(
        ...,
        description="Password reset token from email",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate new password strength."""
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


# Helper functions
async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """
    Authenticate user by email and password.
    
    Args:
        session: Database session.
        email: User's email address.
        password: Plain text password to verify.
    
    Returns:
        User object if authentication succeeds, None otherwise.
    """
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Prevent timing attacks by still computing hash
        verify_password(password, "$2b$12$dummy.hash.to.prevent.timing.attack")
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def create_user_tokens(
    user: User,
    device_id: Optional[str] = None,
) -> TokenResponse:
    """
    Create access and refresh tokens for user.
    
    Args:
        user: User object.
        device_id: Optional device identifier for token tracking.
    
    Returns:
        TokenResponse with both tokens.
    """
    # Token payload
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
    }
    
    if device_id:
        token_data["device_id"] = device_id
    
    # Create tokens
    access_token = create_token(
        data=token_data,
        token_type=TokenType.ACCESS,
    )
    refresh_token = create_token(
        data=token_data,
        token_type=TokenType.REFRESH,
    )
    
    # Store refresh token in cache for revocation support
    await cache_manager.set(
        f"refresh_token:{user.id}:{device_id or 'default'}",
        refresh_token,
        ttl=settings.refresh_token_expire_days * 24 * 3600,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


# API Endpoints
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email verification",
)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    tenant_id: Optional[str] = None,  # From middleware
) -> UserResponse:
    """
    Register a new user account.
    
    The user will receive an email verification link and must verify
    their email before being able to log in.
    
    Args:
        request: Registration details.
        background_tasks: FastAPI background tasks.
        session: Database session.
        tenant_id: Optional tenant ID for multi-tenant apps.
    
    Returns:
        Created user details.
    
    Raises:
        HTTPException: If email already exists or validation fails.
    """
    try:
        # Check if user exists
        existing = await session.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        
        # Create user
        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            tenant_id=tenant_id,
            is_active=True,
            is_verified=False,  # Require email verification
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Send verification email in background
        verification_token = create_token(
            data={"sub": str(user.id), "purpose": "email_verification"},
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(hours=24),
        )
        
        # In production, send actual email
        background_tasks.add_task(
            send_verification_email,
            user.email,
            verification_token,
        )
        
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse.model_validate(user)
        
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and receive JWT tokens",
)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Authenticate user and issue JWT tokens.
    
    Uses OAuth2 password flow for compatibility with OpenAPI tools.
    The username field should contain the email address.
    
    Args:
        request: FastAPI request object for device info.
        form_data: OAuth2 password credentials.
        session: Database session.
    
    Returns:
        Access and refresh tokens.
    
    Raises:
        HTTPException: If authentication fails.
    """
    # Rate limiting check
    client_ip = request.client.host
    login_key = f"login_attempts:{client_ip}:{form_data.username}"
    attempts = await cache_manager.get(login_key) or 0
    
    if attempts >= 5:
        logger.warning(f"Too many login attempts from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    
    # Authenticate user
    user = await authenticate_user(
        session,
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password,
    )
    
    if not user:
        # Increment failed attempts
        await cache_manager.increment(login_key)  # Track failed attempt
        await cache_manager.expire(login_key, 300)  # Expire in 5 minutes
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    if not user.is_verified and settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    
    # Clear failed attempts on successful login
    await cache_manager.delete(login_key)
    
    # Extract device info from user agent
    device_id = request.headers.get("X-Device-ID")
    
    # Create tokens
    tokens = await create_user_tokens(user, device_id)
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    
    logger.info(f"User logged in: {user.email}")
    
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use refresh token to obtain new access token",
)
async def refresh_access_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Refresh access token using valid refresh token.
    
    Args:
        request: Refresh token request.
        session: Database session.
    
    Returns:
        New access and refresh tokens.
    
    Raises:
        HTTPException: If refresh token is invalid or expired.
    """
    try:
        # Decode refresh token
        payload = decode_token(request.refresh_token, TokenType.REFRESH)
        user_id = payload.get("sub")
        device_id = payload.get("device_id", "default")
        
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Check if refresh token is still valid in cache
        cached_token = await cache_manager.get(
            f"refresh_token:{user_id}:{device_id}"
        )
        
        if cached_token != request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        
        # Get user from database
        user = await session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Create new tokens
        tokens = await create_user_tokens(user, device_id)
        
        logger.info(f"Tokens refreshed for user: {user.email}")
        
        return tokens
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Revoke tokens and clear session",
    response_model=None,
)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
    refresh_token: Optional[str] = None,
) -> None:
    """
    Logout user by revoking tokens.
    
    Args:
        current_user: Current authenticated user.
        refresh_token: Optional refresh token to revoke.
    
    Returns:
        No content on success.
    """
    # Revoke all refresh tokens for user
    pattern = f"refresh_token:{current_user.id}:*"
    await cache_manager.delete_pattern(pattern)
    
    # Add access token to blacklist (optional, for extra security)
    # This requires extracting token from request headers
    
    logger.info(f"User logged out: {current_user.email}")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get details of currently authenticated user",
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """
    Get current authenticated user details.
    
    Args:
        current_user: Current authenticated user from token.
    
    Returns:
        User details.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description="Send password reset email to user",
)
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """
    Initiate password reset flow.
    
    Always returns success to prevent email enumeration attacks.
    
    Args:
        request: Password reset request with email.
        background_tasks: FastAPI background tasks.
        session: Database session.
    
    Returns:
        Success message.
    """
    # Get user (but don't reveal if exists)
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if user and user.is_active:
        # Create reset token
        reset_token = create_token(
            data={
                "sub": str(user.id),
                "purpose": "password_reset",
                "email": user.email,
            },
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(hours=1),
        )
        
        # Store token in cache to prevent reuse
        await cache_manager.set(
            f"password_reset:{user.id}",
            reset_token,
            ttl=3600,  # 1 hour
        )
        
        # Send email in background
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            reset_token,
        )
        
        logger.info(f"Password reset requested for: {user.email}")
    
    # Always return success to prevent enumeration
    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Complete password reset with token",
)
async def reset_password(
    request: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """
    Complete password reset using token from email.
    
    Args:
        request: Password reset confirmation with token and new password.
        session: Database session.
    
    Returns:
        Success message.
    
    Raises:
        HTTPException: If token is invalid or expired.
    """
    try:
        # Decode reset token
        payload = decode_token(request.token, TokenType.ACCESS)
        
        if payload.get("purpose") != "password_reset":
            raise ValueError("Invalid token purpose")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Check if token hasn't been used
        cached_token = await cache_manager.get(f"password_reset:{user_id}")
        if cached_token != request.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has already been used",
            )
        
        # Get user and update password
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        user.hashed_password = get_password_hash(request.new_password)
        session.add(user)
        
        # Invalidate token
        await cache_manager.delete(f"password_reset:{user_id}")
        
        # Revoke all refresh tokens (security measure)
        await cache_manager.delete_pattern(f"refresh_token:{user_id}:*")
        
        await session.commit()
        
        logger.info(f"Password reset completed for: {user.email}")
        
        return {"message": "Password has been reset successfully"}
        
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )


# Background tasks (in production, use proper email service)
async def send_verification_email(email: str, token: str) -> None:
    """Send email verification link."""
    frontend_url = getattr(settings, "frontend_url", "http://localhost:3000")
    verification_url = f"{frontend_url}/verify-email?token={token}"
    logger.info(f"Verification email would be sent to {email}: {verification_url}")
    # TODO: Implement actual email sending


async def send_password_reset_email(email: str, token: str) -> None:
    """Send password reset link."""
    frontend_url = getattr(settings, "frontend_url", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password?token={token}"
    logger.info(f"Password reset email would be sent to {email}: {reset_url}")
    # TODO: Implement actual email sending