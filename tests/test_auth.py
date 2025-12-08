# -*- coding: utf-8 -*-

"""
Unit tests for authentication API endpoints.

Tests cover:
- User registration
- User login
- Email verification
- User data CRUD operations
"""

import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRoot:
    """Test root endpoint."""

    async def test_root(self, client: AsyncClient):
        """Test root endpoint returns welcome message."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]


class TestUserRegistration:
    """Test user registration endpoint."""

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_register_user_success(
        self, mock_verify: AsyncMock, client: AsyncClient
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
        self, mock_verify: AsyncMock, client: AsyncClient
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
    async def test_login_success(self, mock_verify: AsyncMock, client: AsyncClient):
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

    async def test_get_user_data_unauthorized(self, client: AsyncClient):
        """Test accessing user data without authentication."""
        response = await client.get("/api/user-data")
        assert response.status_code == 401

    async def test_update_user_data_unauthorized(self, client: AsyncClient):
        """Test updating user data without authentication."""
        response = await client.put(
            "/api/user-data", json={"text_value": "test content"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.auth",
        preview=False,
    )
