# -*- coding: utf-8 -*-

"""
Integration tests for application API endpoints.

Tests cover:
- Health check endpoint
- Root endpoint
- User registration API
- User login API
- Protected routes access control
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
        """Test root endpoint returns HTML homepage."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Hello World" in response.text
        assert "FastAPI Auth" in response.text


class TestPageRoutes:
    """Test HTML page routes."""

    async def test_signup_page(self, client: AsyncClient):
        """Test signup page renders correctly."""
        response = await client.get("/signup")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Create Account" in response.text

    async def test_signin_page(self, client: AsyncClient):
        """Test signin page renders correctly."""
        response = await client.get("/signin")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Sign In" in response.text

    async def test_app_page(self, client: AsyncClient):
        """Test app page renders correctly."""
        response = await client.get("/app")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Your Personal Data" in response.text

    async def test_forgot_password_page(self, client: AsyncClient):
        """Test forgot password page renders correctly."""
        response = await client.get("/forgot-password")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Forgot Password" in response.text

    async def test_reset_password_page(self, client: AsyncClient):
        """Test reset password page renders correctly."""
        response = await client.get("/reset-password")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Reset Password" in response.text


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
        # User is inactive until email verification
        assert data["is_active"] is False
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

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_register")
    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_login_success(
        self,
        mock_verify: AsyncMock,
        mock_register: AsyncMock,
        client: AsyncClient,
    ):
        """Test successful user login."""
        mock_verify.return_value = None
        mock_register.return_value = None  # Skip deactivation for this test

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

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_login_unverified_user_fails(
        self,
        mock_verify: AsyncMock,
        client: AsyncClient,
    ):
        """Test login fails for user who hasn't verified email."""
        mock_verify.return_value = None

        # Register a user (will be inactive until verified)
        email = f"unverified_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPass123!"
        register_data = {"email": email, "password": password}
        response = await client.post("/api/auth/register", json=register_data)
        assert response.status_code == 201
        assert response.json()["is_active"] is False

        # Attempt to login - should fail because user is inactive
        login_data = {"username": email, "password": password}
        response = await client.post("/api/auth/login", data=login_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"


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

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_register")
    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_get_users_me(
        self,
        mock_verify: AsyncMock,
        mock_register: AsyncMock,
        client: AsyncClient,
    ):
        """Test getting current user info with valid token."""
        mock_verify.return_value = None
        mock_register.return_value = None  # Skip deactivation for this test

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


class TestPasswordReset:
    """Test password reset endpoints."""

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_forgot_password")
    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_forgot_password_existing_email(
        self,
        mock_verify: AsyncMock,
        mock_forgot: AsyncMock,
        client: AsyncClient,
    ):
        """Test forgot password for existing user."""
        mock_verify.return_value = None
        mock_forgot.return_value = None

        # Register a user first
        email = f"forgot_test_{uuid.uuid4().hex[:8]}@example.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "TestPass123!"}
        )

        # Request password reset
        response = await client.post(
            "/api/auth/forgot-password", json={"email": email}
        )

        # Should return 202 (accepted) regardless of email existence
        assert response.status_code == 202

    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test forgot password for non-existent email (should not reveal)."""
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        # Should still return 202 to not reveal if email exists
        assert response.status_code == 202

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test reset password with invalid token."""
        response = await client.post(
            "/api/auth/reset-password",
            json={"token": "invalid_token", "password": "NewPass123!"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "RESET_PASSWORD_BAD_TOKEN"


class TestChangePassword:
    """Test change password endpoint."""

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_register")
    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_change_password_success(
        self,
        mock_verify: AsyncMock,
        mock_register: AsyncMock,
        client: AsyncClient,
    ):
        """Test changing password with correct current password."""
        mock_verify.return_value = None
        mock_register.return_value = None

        # Register and login
        email = f"change_pw_{uuid.uuid4().hex[:8]}@example.com"
        old_password = "OldPass123!"
        new_password = "NewPass456!"

        await client.post(
            "/api/auth/register", json={"email": email, "password": old_password}
        )
        login_response = await client.post(
            "/api/auth/login", data={"username": email, "password": old_password}
        )
        token = login_response.json()["access_token"]

        # Change password
        response = await client.post(
            "/api/auth/change-password",
            json={"current_password": old_password, "new_password": new_password},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

        # Verify old password no longer works
        login_old = await client.post(
            "/api/auth/login", data={"username": email, "password": old_password}
        )
        assert login_old.status_code == 400

        # Verify new password works
        login_new = await client.post(
            "/api/auth/login", data={"username": email, "password": new_password}
        )
        assert login_new.status_code == 200

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_register")
    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_change_password_wrong_current(
        self,
        mock_verify: AsyncMock,
        mock_register: AsyncMock,
        client: AsyncClient,
    ):
        """Test changing password with wrong current password."""
        mock_verify.return_value = None
        mock_register.return_value = None

        # Register and login
        email = f"wrong_pw_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPass123!"

        await client.post(
            "/api/auth/register", json={"email": email, "password": password}
        )
        login_response = await client.post(
            "/api/auth/login", data={"username": email, "password": password}
        )
        token = login_response.json()["access_token"]

        # Try to change password with wrong current password
        response = await client.post(
            "/api/auth/change-password",
            json={"current_password": "WrongPassword!", "new_password": "NewPass456!"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "CHANGE_PASSWORD_INVALID_CURRENT"

    async def test_change_password_unauthorized(self, client: AsyncClient):
        """Test changing password without authentication."""
        response = await client.post(
            "/api/auth/change-password",
            json={"current_password": "old", "new_password": "newpass123"},
        )
        assert response.status_code == 401


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.app",
        preview=False,
    )
