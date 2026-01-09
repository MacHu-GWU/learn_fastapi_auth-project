# -*- coding: utf-8 -*-

"""
Pydantic schemas for request/response validation.

Defines schemas for:
- User authentication (fastapi-users)
- User data CRUD operations
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi_users import schemas
from pydantic import BaseModel, Field


# =============================================================================
# User Schemas (for fastapi-users)
# =============================================================================
class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user."""

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data."""

    pass


# =============================================================================
# User Data Schemas
# =============================================================================
class UserDataRead(BaseModel):
    """Schema for reading user data."""

    user_id: uuid.UUID
    text_value: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDataUpdate(BaseModel):
    """Schema for updating user data."""

    text_value: str = Field(..., description="User's text content")


# =============================================================================
# Token Schemas
# =============================================================================
class TokenResponse(BaseModel):
    """Schema for token response after login."""

    access_token: str
    token_type: str = "bearer"


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response."""

    access_token: str
    token_type: str = "bearer"


# =============================================================================
# Password Change Schema
# =============================================================================
class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""

    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password")


# =============================================================================
# General Response Schemas
# =============================================================================
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    detail: Optional[str] = None
