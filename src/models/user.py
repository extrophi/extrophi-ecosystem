"""
User model for authentication and authorization.

This module defines the User SQLModel for database storage
with all necessary fields for multi-tenant authentication.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, String, JSON
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """Base user model with common fields."""
    
    email: EmailStr = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    full_name: str = Field(min_length=1, max_length=100)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    role: str = Field(default="user", max_length=50)
    tenant_id: Optional[str] = Field(default=None, max_length=100, index=True)
    bio: Optional[str] = Field(default=None, max_length=500)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    user_metadata: Optional[dict] = Field(default=None, sa_column=Column("user_metadata", JSON, nullable=True))


class User(UserBase, table=True):
    """User database model."""
    
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_login: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)  # Soft delete


class UserCreate(SQLModel):
    """Schema for creating a new user."""
    
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    tenant_id: Optional[str] = None


class UserUpdate(SQLModel):
    """Schema for updating user information."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    user_metadata: Optional[dict] = None