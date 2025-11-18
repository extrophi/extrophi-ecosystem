"""
User management endpoints for CRUD operations.

This module provides comprehensive user management functionality including
listing, searching, updating, and deleting users with proper authorization
and multi-tenant support.

Endpoints:
    GET /users - List users with pagination and filtering
    GET /users/search - Search users by name or email
    GET /users/{user_id} - Get specific user details
    PUT /users/{user_id} - Update user information
    DELETE /users/{user_id} - Delete user (soft delete)
    POST /users/{user_id}/activate - Activate user account
    POST /users/{user_id}/deactivate - Deactivate user account
    PUT /users/{user_id}/role - Update user role (admin only)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crud_base import CRUDBase
from src.core.database import get_session
from src.core.security import (
    UserRole,
    get_current_active_user,
    get_current_user_tenant,
    require_role,
)
from src.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Users"])


# Pydantic schemas
class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = Field(None, description="New email address")
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's full name",
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="User biography or description",
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL to user's avatar image",
    )
    user_metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional user metadata",
    )


class UserResponse(BaseModel):
    """User response schema with full details."""
    
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""
    
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class RoleUpdate(BaseModel):
    """Role update request schema."""
    
    role: UserRole = Field(..., description="New user role")


# CRUD instance
class UserCRUD(CRUDBase[User, UserUpdate, UserUpdate]):
    """User-specific CRUD operations."""
    
    async def get_by_email(
        self,
        session: AsyncSession,
        *,
        email: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[User]:
        """Get user by email address."""
        return await self.get_by_field(
            session,
            field="email",
            value=email,
            tenant_id=tenant_id,
        )


user_crud = UserCRUD(User)


# API Endpoints
@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users",
    description="Get paginated list of users with optional filtering",
)
async def list_users(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    is_active: Annotated[Optional[bool], Query(description="Filter by active status")] = None,
    is_verified: Annotated[Optional[bool], Query(description="Filter by verification status")] = None,
    role: Annotated[Optional[UserRole], Query(description="Filter by role")] = None,
    order_by: Annotated[str, Query(description="Sort field (prefix with - for DESC)")] = "-created_at",
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> UserListResponse:
    """
    List users with pagination and filtering.
    
    Regular users can only see other active users in their tenant.
    Admins can see all users including inactive ones.
    
    Args:
        page: Page number (1-based).
        per_page: Number of items per page.
        is_active: Filter by active status.
        is_verified: Filter by email verification status.
        role: Filter by user role.
        order_by: Sort field and direction.
        current_user: Current authenticated user.
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        Paginated list of users.
    """
    # Build filters
    filters = {}
    
    # Non-admins can only see active users
    if current_user.role != UserRole.ADMIN:
        filters["is_active"] = True
    elif is_active is not None:
        filters["is_active"] = is_active
    
    if is_verified is not None:
        filters["is_verified"] = is_verified
    
    if role is not None:
        filters["role"] = role.value
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get users
    users = await user_crud.get_multi(
        session,
        skip=skip,
        limit=per_page,
        tenant_id=tenant_id,
        order_by=order_by,
        filters=filters,
    )
    
    # Get total count
    total = await user_crud.count(session, tenant_id=tenant_id, filters=filters)
    
    # Calculate pages
    pages = (total + per_page - 1) // per_page
    
    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/search",
    response_model=list[UserResponse],
    summary="Search users",
    description="Search users by name or email",
)
async def search_users(
    q: Annotated[str, Query(min_length=2, description="Search query")] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Maximum results")] = 10,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> list[UserResponse]:
    """
    Search users by name or email.
    
    Args:
        q: Search query (minimum 2 characters).
        limit: Maximum number of results.
        current_user: Current authenticated user.
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        List of matching users.
    """
    # Search in name and email fields
    users = await user_crud.search(
        session,
        query=q,
        fields=["full_name", "email"],
        limit=limit,
        tenant_id=tenant_id,
    )
    
    # Filter out inactive users for non-admins
    if current_user.role != UserRole.ADMIN:
        users = [u for u in users if u.is_active]
    
    return [UserResponse.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details",
    description="Get detailed information about a specific user",
)
async def get_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> UserResponse:
    """
    Get detailed user information.
    
    Args:
        user_id: User ID to retrieve.
        current_user: Current authenticated user.
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        User details.
    
    Raises:
        HTTPException: If user not found or access denied.
    """
    user = await user_crud.get(session, user_id, tenant_id=tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Non-admins cannot see inactive users (except themselves)
    if (
        not user.is_active
        and current_user.role != UserRole.ADMIN
        and user.id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information",
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> UserResponse:
    """
    Update user information.
    
    Users can update their own profile. Admins can update any user.
    
    Args:
        user_id: User ID to update.
        user_update: Fields to update.
        current_user: Current authenticated user.
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        Updated user details.
    
    Raises:
        HTTPException: If user not found or access denied.
    """
    # Check permissions
    if user_id != str(current_user.id) and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    
    # Get user
    user = await user_crud.get(session, user_id, tenant_id=tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if email is being changed
    if user_update.email and user_update.email != user.email:
        # Check if new email already exists
        existing = await user_crud.get_by_email(
            session,
            email=user_update.email,
            tenant_id=tenant_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )
        
        # Mark as unverified if email changes
        user.is_verified = False
    
    # Update user
    updated_user = await user_crud.update(
        session,
        id=user_id,
        obj_in=user_update,
        tenant_id=tenant_id,
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    logger.info(f"User updated: {updated_user.email} by {current_user.email}")
    
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete user",
    description="Soft delete a user account",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> None:
    """
    Soft delete a user account.
    
    Only admins can delete users. The user is marked as inactive rather
    than being permanently deleted.
    
    Args:
        user_id: User ID to delete.
        current_user: Current authenticated user (admin).
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Raises:
        HTTPException: If user not found or trying to delete self.
    """
    # Prevent self-deletion
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    # Get user
    user = await user_crud.get(session, user_id, tenant_id=tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Soft delete by deactivating
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    
    logger.info(f"User deleted: {user.email} by {current_user.email}")


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user",
    description="Activate a deactivated user account",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def activate_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> UserResponse:
    """
    Activate a deactivated user account.
    
    Args:
        user_id: User ID to activate.
        current_user: Current authenticated user (admin).
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        Updated user details.
    
    Raises:
        HTTPException: If user not found.
    """
    user = await user_crud.get(session, user_id, tenant_id=tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.is_active = True
    user.deleted_at = None
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"User activated: {user.email} by {current_user.email}")
    
    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate user",
    description="Deactivate a user account",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def deactivate_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> UserResponse:
    """
    Deactivate a user account.
    
    Args:
        user_id: User ID to deactivate.
        current_user: Current authenticated user (admin).
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        Updated user details.
    
    Raises:
        HTTPException: If user not found or trying to deactivate self.
    """
    # Prevent self-deactivation
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    user = await user_crud.get(session, user_id, tenant_id=tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.is_active = False
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"User deactivated: {user.email} by {current_user.email}")
    
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role",
    description="Change a user's role (admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def update_user_role(
    user_id: str,
    role_update: RoleUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    tenant_id: Annotated[Optional[str], Depends(get_current_user_tenant)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> UserResponse:
    """
    Update a user's role.
    
    Args:
        user_id: User ID to update.
        role_update: New role assignment.
        current_user: Current authenticated user (admin).
        tenant_id: Current user's tenant ID.
        session: Database session.
    
    Returns:
        Updated user details.
    
    Raises:
        HTTPException: If user not found or trying to change own role.
    """
    # Prevent changing own role
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )
    
    user = await user_crud.get(session, user_id, tenant_id=tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update role
    user.role = role_update.role.value
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(
        f"User role updated: {user.email} to {role_update.role} "
        f"by {current_user.email}"
    )
    
    return UserResponse.model_validate(user)