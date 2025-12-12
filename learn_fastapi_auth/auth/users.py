# -*- coding: utf-8 -*-

"""
FastAPI-Users configuration.

Provides user management, authentication backends, and user manager setup.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learn_fastapi_auth.config import config
from learn_fastapi_auth.database import get_async_session
from learn_fastapi_auth.models import Token, User, UserData


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
):
    """Dependency for getting the user database."""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    User manager with custom logic for registration and verification.
    """

    reset_password_token_secret = config.secret_key
    verification_token_secret = config.secret_key

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """Called after a user successfully registers."""
        print(f"User {user.id} has registered.")
        # Send verification email first (requires user to be active)
        await self.request_verify(user, request)

        # Then set user as inactive until email is verified
        session: AsyncSession = self.user_db.session
        user.is_active = False
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"User {user.id} set to inactive until email verified.")

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        """Called after a user requests password reset."""
        from learn_fastapi_auth.auth.email import send_password_reset_email

        await send_password_reset_email(user.email, token)
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        """Called after a user requests email verification."""
        from learn_fastapi_auth.auth.email import send_verification_email

        await send_verification_email(user.email, token)
        print(f"Verification requested for user {user.id}. Token: {token}")

    async def on_after_verify(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """Called after a user is verified. Activates account and creates UserData."""
        session: AsyncSession = self.user_db.session

        # Activate the user account
        user.is_active = True
        session.add(user)
        print(f"User {user.id} has been verified and activated.")

        # Create UserData record for the verified user
        # Check if user_data already exists
        result = await session.execute(
            select(UserData).where(UserData.user_id == user.id)
        )
        existing_data = result.scalar_one_or_none()

        if not existing_data:
            user_data = UserData(user_id=user.id, text_value="")
            session.add(user_data)
            print(f"Created UserData for user {user.id}")

        await session.commit()


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    """Dependency for getting the user manager."""
    yield UserManager(user_db)


# =============================================================================
# Authentication Backend
# =============================================================================
bearer_transport = BearerTransport(tokenUrl="api/auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy with configured lifetime."""
    return JWTStrategy(
        secret=config.secret_key,
        lifetime_seconds=config.access_token_lifetime,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# =============================================================================
# FastAPI Users Instance
# =============================================================================
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Dependency for getting current active user
current_active_user = fastapi_users.current_user(active=True)

# Dependency for getting current verified user
current_verified_user = fastapi_users.current_user(active=True, verified=True)


# =============================================================================
# Token Database Management
# =============================================================================
async def store_token(
    session: AsyncSession,
    token_str: str,
    user_id: uuid.UUID,
) -> Token:
    """Store a JWT token in the database."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=config.access_token_lifetime
    )
    token = Token(token=token_str, user_id=user_id, expires_at=expires_at)
    session.add(token)
    await session.commit()
    return token


async def delete_token(
    session: AsyncSession,
    token_str: str,
) -> bool:
    """Delete a token from the database (logout)."""
    result = await session.execute(select(Token).where(Token.token == token_str))
    token = result.scalar_one_or_none()
    if token:
        await session.delete(token)
        await session.commit()
        return True
    return False


async def validate_token_in_db(
    session: AsyncSession,
    token_str: str,
) -> bool:
    """Check if a token exists and is not expired."""
    result = await session.execute(select(Token).where(Token.token == token_str))
    token = result.scalar_one_or_none()
    if token:
        # Handle both timezone-aware and naive datetimes (SQLite stores naive)
        now = datetime.now(timezone.utc)
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > now:
            return True
    return False
