"""
API Key Authentication Module

Provides secure API key generation, validation, and rate limiting.

Features:
- Secure key generation (32+ characters using secrets module)
- SHA-256 hashed storage (never stores plaintext keys)
- Authorization middleware (FastAPI dependency injection)
- Rate limiting (1000 requests/hour per key by default)
- Key management (create, list, revoke)
- User association (keys tied to user accounts)

Usage:
    from backend.auth.api_keys import require_api_key

    @app.get("/protected")
    async def protected_endpoint(user_id: str = Depends(require_api_key)):
        return {"user_id": user_id}
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from backend.db.connection import get_session
from backend.db.models import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyModel,
    APIKeyORM,
)


class APIKeyAuth:
    """
    API Key Authentication and Management Class

    Handles:
    - Secure API key generation with configurable length
    - SHA-256 hashing for secure storage
    - Rate limiting enforcement
    - Key validation and user authentication
    - Key lifecycle management (create, revoke, list)
    """

    KEY_PREFIX = "extro_live_"
    KEY_LENGTH = 48  # Total random bytes (results in ~64 char string with prefix)
    HASH_ALGORITHM = "sha256"
    DEFAULT_RATE_LIMIT = 1000  # Requests per hour
    DEFAULT_WINDOW_SECONDS = 3600  # 1 hour

    @classmethod
    def generate_key(cls) -> tuple[str, str, str]:
        """
        Generate a new secure API key using secrets module.

        Returns:
            tuple: (full_key, key_prefix, key_hash)
                - full_key: Complete API key (e.g., "extro_live_abc123...")
                - key_prefix: First 8-12 chars for identification
                - key_hash: SHA-256 hash for database storage

        Example:
            >>> full_key, prefix, hash_val = APIKeyAuth.generate_key()
            >>> print(f"Key: {full_key}")
            extro_live_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567
        """
        # Generate cryptographically secure random string
        random_part = secrets.token_urlsafe(cls.KEY_LENGTH)

        # Construct full key with prefix
        full_key = f"{cls.KEY_PREFIX}{random_part}"

        # Extract prefix for identification (first 15 chars: "extro_live_" + 4 random chars)
        key_prefix = full_key[:15]

        # Generate SHA-256 hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        return full_key, key_prefix, key_hash

    @classmethod
    def hash_key(cls, api_key: str) -> str:
        """
        Hash an API key using SHA-256.

        Args:
            api_key: The API key to hash

        Returns:
            str: SHA-256 hash of the key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    @classmethod
    def create_api_key(
        cls,
        db: Session,
        user_id: UUID,
        request: APIKeyCreateRequest,
    ) -> APIKeyCreateResponse:
        """
        Create a new API key for a user.

        Args:
            db: Database session
            user_id: User ID to associate the key with
            request: API key creation request with key_name, expiration, rate limit

        Returns:
            APIKeyCreateResponse: Created key info with full API key (shown only once)

        Raises:
            HTTPException: If key_name already exists for user
        """
        # Check if key_name already exists for this user
        stmt = select(APIKeyORM).where(
            and_(APIKeyORM.user_id == user_id, APIKeyORM.key_name == request.key_name)
        )
        result = db.execute(stmt)
        existing_key = result.scalar_one_or_none()

        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"API key with name '{request.key_name}' already exists",
            )

        # Generate new API key
        full_key, key_prefix, key_hash = cls.generate_key()

        # Calculate expiration if requested
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Create database record
        api_key_orm = APIKeyORM(
            user_id=user_id,
            key_name=request.key_name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            rate_limit_requests=request.rate_limit_requests or cls.DEFAULT_RATE_LIMIT,
            rate_limit_window_seconds=cls.DEFAULT_WINDOW_SECONDS,
            expires_at=expires_at,
        )

        db.add(api_key_orm)
        db.commit()
        db.refresh(api_key_orm)

        # Return response with full key (only time it's ever shown)
        return APIKeyCreateResponse(
            id=str(api_key_orm.id),
            key_name=api_key_orm.key_name,
            api_key=full_key,  # CRITICAL: Only shown once, never stored in plaintext
            key_prefix=api_key_orm.key_prefix,
            expires_at=api_key_orm.expires_at,
            rate_limit_requests=api_key_orm.rate_limit_requests,
            created_at=api_key_orm.created_at,
        )

    @classmethod
    def validate_key(
        cls,
        db: Session,
        api_key: str,
        check_rate_limit: bool = True,
    ) -> tuple[str, APIKeyORM]:
        """
        Validate an API key and check rate limiting.

        Args:
            db: Database session
            api_key: The API key to validate
            check_rate_limit: Whether to enforce rate limiting (default: True)

        Returns:
            tuple: (user_id, api_key_orm)

        Raises:
            HTTPException: If key is invalid, revoked, expired, or rate limited
        """
        # Hash the provided key
        key_hash = cls.hash_key(api_key)

        # Query database for key
        stmt = select(APIKeyORM).where(APIKeyORM.key_hash == key_hash)
        result = db.execute(stmt)
        api_key_orm = result.scalar_one_or_none()

        # Check if key exists
        if not api_key_orm:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if key is revoked
        if api_key_orm.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if key is active
        if not api_key_orm.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration
        if api_key_orm.expires_at and api_key_orm.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Rate limiting check
        if check_rate_limit:
            cls._check_rate_limit(db, api_key_orm)

        # Update usage statistics
        api_key_orm.last_used_at = datetime.utcnow()
        api_key_orm.request_count += 1

        # Increment current window usage count
        api_key_orm.current_usage_count += 1

        db.commit()
        db.refresh(api_key_orm)

        return str(api_key_orm.user_id), api_key_orm

    @classmethod
    def _check_rate_limit(cls, db: Session, api_key_orm: APIKeyORM) -> None:
        """
        Check if the API key has exceeded its rate limit.

        Implements a sliding window rate limiter:
        - Resets window if expired
        - Checks if current usage is within limit
        - Raises 429 if limit exceeded

        Args:
            db: Database session
            api_key_orm: The API key ORM object

        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        now = datetime.utcnow()

        # Initialize window if not set
        if not api_key_orm.rate_limit_window_start:
            api_key_orm.rate_limit_window_start = now
            api_key_orm.current_usage_count = 0
            return

        # Calculate window end
        window_end = api_key_orm.rate_limit_window_start + timedelta(
            seconds=api_key_orm.rate_limit_window_seconds
        )

        # Reset window if expired
        if now > window_end:
            api_key_orm.rate_limit_window_start = now
            api_key_orm.current_usage_count = 0
            return

        # Check if limit exceeded
        if api_key_orm.current_usage_count >= api_key_orm.rate_limit_requests:
            # Calculate time until window resets
            time_until_reset = (window_end - now).total_seconds()

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {int(time_until_reset)} seconds.",
                headers={
                    "X-RateLimit-Limit": str(api_key_orm.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_end.timestamp())),
                    "Retry-After": str(int(time_until_reset)),
                },
            )

    @classmethod
    def list_keys(
        cls,
        db: Session,
        user_id: UUID,
        include_revoked: bool = False,
    ) -> APIKeyListResponse:
        """
        List all API keys for a user.

        Args:
            db: Database session
            user_id: User ID to list keys for
            include_revoked: Whether to include revoked keys (default: False)

        Returns:
            APIKeyListResponse: List of API keys (without sensitive data)
        """
        # Build query
        conditions = [APIKeyORM.user_id == user_id]
        if not include_revoked:
            conditions.append(APIKeyORM.is_revoked == False)

        stmt = select(APIKeyORM).where(and_(*conditions)).order_by(APIKeyORM.created_at.desc())

        result = db.execute(stmt)
        api_keys = result.scalars().all()

        # Convert to response models
        key_models = [
            APIKeyModel(
                id=str(key.id),
                user_id=str(key.user_id),
                key_name=key.key_name,
                key_prefix=key.key_prefix,
                is_active=key.is_active,
                is_revoked=key.is_revoked,
                rate_limit_requests=key.rate_limit_requests,
                rate_limit_window_seconds=key.rate_limit_window_seconds,
                current_usage_count=key.current_usage_count,
                last_used_at=key.last_used_at,
                request_count=key.request_count,
                expires_at=key.expires_at,
                created_at=key.created_at,
                updated_at=key.updated_at,
                revoked_at=key.revoked_at,
            )
            for key in api_keys
        ]

        return APIKeyListResponse(keys=key_models, total=len(key_models))

    @classmethod
    def revoke_key(cls, db: Session, user_id: UUID, key_id: UUID) -> bool:
        """
        Revoke an API key.

        Args:
            db: Database session
            user_id: User ID that owns the key
            key_id: API key ID to revoke

        Returns:
            bool: True if revoked, False if not found

        Raises:
            HTTPException: If key doesn't belong to user
        """
        # Find the key
        stmt = select(APIKeyORM).where(APIKeyORM.id == key_id)
        result = db.execute(stmt)
        api_key_orm = result.scalar_one_or_none()

        if not api_key_orm:
            return False

        # Verify ownership
        if api_key_orm.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to revoke this API key",
            )

        # Revoke the key (trigger will set revoked_at and is_active=False)
        api_key_orm.is_revoked = True

        db.commit()
        return True

    @classmethod
    def delete_key(cls, db: Session, user_id: UUID, key_id: UUID) -> bool:
        """
        Permanently delete an API key.

        Args:
            db: Database session
            user_id: User ID that owns the key
            key_id: API key ID to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            HTTPException: If key doesn't belong to user
        """
        # Find the key
        stmt = select(APIKeyORM).where(APIKeyORM.id == key_id)
        result = db.execute(stmt)
        api_key_orm = result.scalar_one_or_none()

        if not api_key_orm:
            return False

        # Verify ownership
        if api_key_orm.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this API key",
            )

        # Delete the key
        db.delete(api_key_orm)
        db.commit()
        return True


# ============================================================================
# FastAPI Dependency Injection
# ============================================================================


async def require_api_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_session),
) -> str:
    """
    FastAPI dependency for protecting endpoints with API key authentication.

    Validates the API key from the Authorization header and returns the user_id.

    Usage:
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(require_api_key)):
            return {"user_id": user_id}

    Args:
        authorization: Authorization header (format: "Bearer sk_live_...")
        db: Database session (injected)

    Returns:
        str: User ID associated with the valid API key

    Raises:
        HTTPException: 401 if key is missing, invalid, revoked, or expired
        HTTPException: 429 if rate limit exceeded
    """
    # Check for Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check Bearer scheme
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <api_key>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract API key
    api_key = authorization.replace("Bearer ", "", 1).strip()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key in Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate key and get user_id
    user_id, _ = await APIKeyAuth.validate_key(db, api_key, check_rate_limit=True)

    return user_id


async def optional_api_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_session),
) -> Optional[str]:
    """
    FastAPI dependency for optional API key authentication.

    Returns user_id if valid key provided, otherwise None.
    Useful for endpoints that have different behavior for authenticated users.

    Usage:
        @app.get("/public-with-perks")
        async def route(user_id: Optional[str] = Depends(optional_api_key)):
            if user_id:
                return {"message": "Welcome back!", "user_id": user_id}
            return {"message": "Hello, guest!"}

    Args:
        authorization: Authorization header (optional)
        db: Database session (injected)

    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    api_key = authorization.replace("Bearer ", "", 1).strip()
    if not api_key:
        return None

    try:
        user_id, _ = await APIKeyAuth.validate_key(db, api_key, check_rate_limit=True)
        return user_id
    except HTTPException:
        return None
