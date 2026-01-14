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
    is_oauth_user: bool = False

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override to compute is_oauth_user from firebase_uid."""
        # Check if obj has firebase_uid attribute (from ORM model)
        if hasattr(obj, "firebase_uid"):
            # Create a dict copy and add is_oauth_user
            data = {
                "id": obj.id,
                "email": obj.email,
                "is_active": obj.is_active,
                "is_superuser": obj.is_superuser,
                "is_verified": obj.is_verified,
                "created_at": getattr(obj, "created_at", None),
                "updated_at": getattr(obj, "updated_at", None),
                "is_oauth_user": obj.firebase_uid is not None,
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


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
# Firebase Authentication Schemas
# =============================================================================
class FirebaseLoginRequest(BaseModel):
    """Schema for Firebase login request."""

    id_token: str = Field(..., description="Firebase ID token from frontend")


class FirebaseLoginResponse(BaseModel):
    """Schema for Firebase login response."""

    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = Field(
        default=False, description="True if this is a newly created user"
    )
    email: str = Field(..., description="User's email address from Firebase")


# =============================================================================
# General Response Schemas
# =============================================================================
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    detail: Optional[str] = None
