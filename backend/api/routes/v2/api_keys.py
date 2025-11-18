"""
API Key Management Routes

Provides REST endpoints for managing API keys:
- POST /api/keys - Create a new API key
- GET /api/keys - List user's API keys
- DELETE /api/keys/{key_id} - Revoke an API key

All endpoints require authentication via API key (except the first key creation).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.api_keys import APIKeyAuth, require_api_key
from backend.db.connection import get_session
from backend.db.models import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyModel,
)

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


@router.post(
    "",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    description="""
    Create a new API key for the authenticated user.

    **IMPORTANT**: The full API key is returned only once in the response.
    It is never stored in plaintext and cannot be retrieved later.
    Make sure to save it securely.

    **Rate Limiting**: By default, each key allows 1000 requests per hour.
    This can be customized in the request.

    **Expiration**: Keys can optionally expire after a specified number of days.
    """,
)
def create_api_key(
    request: APIKeyCreateRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
) -> APIKeyCreateResponse:
    """
    Create a new API key.

    Requires authentication via an existing API key.
    For the first key, use an alternative authentication method (e.g., username/password).
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format",
        )

    return APIKeyAuth.create_api_key(db, user_uuid, request)


@router.get(
    "",
    response_model=APIKeyListResponse,
    summary="List API keys",
    description="""
    List all API keys for the authenticated user.

    Returns key metadata including:
    - Key name and prefix (for identification)
    - Creation and last usage timestamps
    - Rate limit information
    - Total request count
    - Revocation status

    **Note**: The full API key is never returned (only shown once during creation).
    """,
)
def list_api_keys(
    include_revoked: bool = False,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
) -> APIKeyListResponse:
    """
    List all API keys for the authenticated user.

    Args:
        include_revoked: Whether to include revoked keys in the response
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format",
        )

    return APIKeyAuth.list_keys(db, user_uuid, include_revoked=include_revoked)


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
    description="""
    Revoke an API key permanently.

    Once revoked:
    - The key cannot be used for authentication
    - The action cannot be undone
    - The key remains in the database for audit purposes

    **Note**: You cannot revoke the key you're currently using for authentication.
    Use a different key to revoke others.
    """,
)
def revoke_api_key(
    key_id: UUID,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
) -> None:
    """
    Revoke an API key.

    The key will be marked as revoked and can no longer be used for authentication.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format",
        )

    # Revoke the key
    revoked = APIKeyAuth.revoke_key(db, user_uuid, key_id)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )


@router.get(
    "/{key_id}",
    response_model=APIKeyModel,
    summary="Get API key details",
    description="""
    Get details about a specific API key.

    Returns metadata about the key including:
    - Usage statistics
    - Rate limit information
    - Expiration status

    **Note**: The full API key is never returned.
    """,
)
def get_api_key(
    key_id: UUID,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
) -> APIKeyModel:
    """Get details about a specific API key."""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format",
        )

    # Get all keys and find the requested one
    response = APIKeyAuth.list_keys(db, user_uuid, include_revoked=True)

    for key in response.keys:
        if key.id == str(key_id):
            return key

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="API key not found",
    )
