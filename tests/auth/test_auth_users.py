# -*- coding: utf-8 -*-

"""
Unit tests for learn_fastapi_auth.auth.users module.

Tests cover:
- User registration API
- User login API
- Email verification flow
- Protected routes access control
- Token management functions
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learn_fastapi_auth.auth.users import (
    delete_token,
    get_jwt_strategy,
    store_token,
    validate_token_in_db,
)
from learn_fastapi_auth.models import Token


class TestUserRegistration:
    """Test user registration endpoint."""

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_register_user_success(
        self,
        mock_verify: AsyncMock,
        client: AsyncClient,
    ):
        """Test successful user registration."""
        mock_verify.return_value = None

        user_data = {
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPass123!",
        }
        response = await client.post("/api/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert data["is_active"] is True
        assert data["is_verified"] is False

    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration fails with invalid email."""
        user_data = {"email": "invalid-email", "password": "TestPass123!"}
        response = await client.post("/api/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_register_user_duplicate_email(
        self,
        mock_verify: AsyncMock,
        client: AsyncClient,
    ):
        """Test registration fails with duplicate email."""
        mock_verify.return_value = None

        email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {"email": email, "password": "TestPass123!"}

        # First registration should succeed
        response1 = await client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201

        # Second registration with same email should fail
        response2 = await client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400


class TestUserLogin:
    """Test user login endpoint."""

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_login_success(
        self,
        mock_verify: AsyncMock,
        client: AsyncClient,
    ):
        """Test successful user login."""
        mock_verify.return_value = None

        # First register a user
        email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPass123!"
        register_data = {"email": email, "password": password}
        await client.post("/api/auth/register", json=register_data)

        # Login with form data (OAuth2 password flow)
        login_data = {"username": email, "password": password}
        response = await client.post("/api/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login fails with wrong password."""
        login_data = {"username": "nonexistent@example.com", "password": "wrongpass"}
        response = await client.post("/api/auth/login", data=login_data)

        assert response.status_code == 400


class TestProtectedRoutes:
    """Test protected API routes."""

    async def test_get_user_data_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test accessing user data without authentication."""
        response = await client.get("/api/user-data")
        assert response.status_code == 401

    async def test_update_user_data_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test updating user data without authentication."""
        response = await client.put(
            "/api/user-data", json={"text_value": "test content"}
        )
        assert response.status_code == 401

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_get_users_me(self, mock_verify: AsyncMock, client: AsyncClient):
        """Test getting current user info with valid token."""
        mock_verify.return_value = None

        # Register and login
        email = f"me_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPass123!"
        await client.post(
            "/api/auth/register", json={"email": email, "password": password}
        )
        login_response = await client.post(
            "/api/auth/login", data={"username": email, "password": password}
        )
        token = login_response.json()["access_token"]

        # Get current user info
        response = await client.get(
            "/api/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email


class TestJWTStrategy:
    """Test JWT strategy configuration."""

    def test_get_jwt_strategy(self):
        """Test JWT strategy returns correct configuration."""
        strategy = get_jwt_strategy()
        assert strategy is not None
        assert strategy.lifetime_seconds > 0


class TestTokenManagement:
    """Test token database management functions."""

    async def test_store_token(
        self,
        test_session: AsyncSession,
    ):
        """Test storing a token in database."""
        user_id = uuid.uuid4()
        token_str = f"test_token_{uuid.uuid4().hex}"

        token = await store_token(test_session, token_str, user_id)

        assert token.token == token_str
        assert token.user_id == user_id
        assert token.expires_at > datetime.now(timezone.utc)

    async def test_validate_token_in_db_valid(
        self,
        test_session: AsyncSession,
    ):
        """Test validating a valid token."""
        user_id = uuid.uuid4()
        token_str = f"valid_token_{uuid.uuid4().hex}"

        await store_token(test_session, token_str, user_id)
        is_valid = await validate_token_in_db(test_session, token_str)

        assert is_valid is True

    async def test_validate_token_in_db_not_found(
        self,
        test_session: AsyncSession,
    ):
        """Test validating a non-existent token."""
        is_valid = await validate_token_in_db(test_session, "non_existent_token")
        assert is_valid is False

    async def test_validate_token_in_db_expired(
        self,
        test_session: AsyncSession,
    ):
        """Test validating an expired token."""
        user_id = uuid.uuid4()
        token_str = f"expired_token_{uuid.uuid4().hex}"

        # Manually create expired token
        expired_token = Token(
            token=token_str,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        test_session.add(expired_token)
        await test_session.commit()

        is_valid = await validate_token_in_db(test_session, token_str)
        assert is_valid is False

    async def test_delete_token_success(
        self,
        test_session: AsyncSession,
    ):
        """Test deleting an existing token."""
        user_id = uuid.uuid4()
        token_str = f"delete_token_{uuid.uuid4().hex}"

        await store_token(test_session, token_str, user_id)
        result = await delete_token(test_session, token_str)

        assert result is True

        # Verify token is deleted
        query_result = await test_session.execute(
            select(Token).where(Token.token == token_str)
        )
        assert query_result.scalar_one_or_none() is None

    async def test_delete_token_not_found(
        self,
        test_session: AsyncSession,
    ):
        """Test deleting a non-existent token."""
        result = await delete_token(test_session, "non_existent_token")
        assert result is False


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.auth.users",
        preview=False,
    )
