# -*- coding: utf-8 -*-

"""
Refresh Token Module.

Provides functionality for token refresh mechanism:
- Generate secure refresh tokens
- Store and validate refresh tokens in database
- Revoke refresh tokens (logout)
- Delete all refresh tokens for a user (logout from all devices)

The refresh token mechanism allows users to obtain new access tokens
without re-authenticating, improving user experience while maintaining security.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import config
from .models import RefreshToken


def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    Uses secrets.token_urlsafe() which generates cryptographically secure
    random tokens suitable for security-sensitive applications.

    Returns:
        A 64-character URL-safe random string.
    """
    return secrets.token_urlsafe(48)


async def create_refresh_token(
    session: AsyncSession,
    user_id: uuid.UUID,
    lifetime_seconds: Optional[int] = None,
) -> str:
    """
    Create and store a new refresh token for a user.

    Args:
        session: Database session
        user_id: UUID of the user
        lifetime_seconds: Optional custom lifetime in seconds. If None, uses
            config.refresh_token_lifetime (7 days by default).

    Returns:
        The generated refresh token string
    """
    token_str = generate_refresh_token()
    actual_lifetime = lifetime_seconds if lifetime_seconds is not None else config.refresh_token_lifetime
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=actual_lifetime
    )

    refresh_token = RefreshToken(
        token=token_str,
        user_id=user_id,
        expires_at=expires_at,
    )
    session.add(refresh_token)
    await session.commit()

    return token_str


async def validate_refresh_token(
    session: AsyncSession,
    token_str: str,
) -> Optional[uuid.UUID]:
    """
    Validate a refresh token and return the associated user ID.

    Checks that:
    1. Token exists in database
    2. Token has not expired

    Args:
        session: Database session
        token_str: The refresh token to validate

    Returns:
        User UUID if token is valid, None otherwise
    """
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token_str)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token is None:
        return None

    # Handle both timezone-aware and naive datetimes (SQLite stores naive)
    now = datetime.now(timezone.utc)
    expires_at = refresh_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        # Token has expired, delete it
        await session.delete(refresh_token)
        await session.commit()
        return None

    return refresh_token.user_id


async def revoke_refresh_token(
    session: AsyncSession,
    token_str: str,
) -> bool:
    """
    Revoke (delete) a specific refresh token.

    Used when user logs out from a single device/session.

    Args:
        session: Database session
        token_str: The refresh token to revoke

    Returns:
        True if token was found and deleted, False otherwise
    """
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token_str)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        await session.delete(refresh_token)
        await session.commit()
        return True

    return False


async def revoke_all_user_refresh_tokens(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """
    Revoke all refresh tokens for a user.

    Used when user wants to logout from all devices or
    when a security event requires invalidating all sessions.

    Args:
        session: Database session
        user_id: UUID of the user

    Returns:
        Number of tokens revoked
    """
    result = await session.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    await session.commit()
    return result.rowcount


async def cleanup_expired_tokens(
    session: AsyncSession,
) -> int:
    """
    Delete all expired refresh tokens from the database.

    Can be called periodically (e.g., via cron job) to clean up
    expired tokens and reduce database size.

    Args:
        session: Database session

    Returns:
        Number of tokens deleted
    """
    now = datetime.now(timezone.utc)
    result = await session.execute(
        delete(RefreshToken).where(RefreshToken.expires_at <= now)
    )
    await session.commit()
    return result.rowcount


def get_refresh_token_cookie_settings(lifetime_seconds: Optional[int] = None) -> dict:
    """
    Get cookie settings for refresh token.

    Returns a dictionary of cookie settings that should be used
    when setting the refresh token cookie in responses.

    Args:
        lifetime_seconds: Optional custom lifetime in seconds. If None, uses
            config.refresh_token_lifetime (7 days by default).

    Returns:
        Dictionary with cookie configuration
    """
    actual_lifetime = lifetime_seconds if lifetime_seconds is not None else config.refresh_token_lifetime
    return {
        "key": config.refresh_token_cookie_name,
        "httponly": True,  # JavaScript cannot access this cookie
        "secure": config.refresh_token_cookie_secure,
        "samesite": config.refresh_token_cookie_samesite,
        "max_age": actual_lifetime,
        "path": "/api/auth",  # Only send cookie to auth endpoints
    }
