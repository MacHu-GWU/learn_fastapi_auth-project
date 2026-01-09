# -*- coding: utf-8 -*-

"""
SQLAdmin configuration for admin dashboard.

Provides admin interface for managing users with superuser authentication.
"""

import uuid

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy import select
from fastapi_users.password import PasswordHelper

from learn_fastapi_auth.config import config
from learn_fastapi_auth.database import engine, async_session_maker
from learn_fastapi_auth.models import User


class AdminAuth(AuthenticationBackend):
    """
    Authentication backend for SQLAdmin.

    Uses session-based authentication separate from the main app's JWT auth.
    Only users with is_superuser=True can access the admin panel.
    """

    async def login(self, request: Request) -> bool:
        """
        Validate admin credentials and create session.

        Returns True if login successful, False otherwise.
        """
        form = await request.form()
        email = form.get("username")  # SQLAdmin uses "username" field name
        password = form.get("password")

        if not email or not password:
            return False

        # Query user from database
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                return False

            # Verify password
            password_helper = PasswordHelper()
            verified, _ = password_helper.verify_and_update(
                password, user.hashed_password
            )

            if not verified:
                return False

            # Check if user is superuser
            if not user.is_superuser:
                return False

            # Check if user is active
            if not user.is_active:
                return False

            # Store user_id in session
            request.session.update({"admin_user_id": str(user.id)})
            return True

    async def logout(self, request: Request) -> bool:
        """Clear admin session."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> RedirectResponse | bool:
        """
        Check if current request is authenticated.

        Returns True if authenticated, RedirectResponse to login page otherwise.
        """
        admin_user_id = request.session.get("admin_user_id")

        if not admin_user_id:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        # Verify user still exists and is still a superuser
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == admin_user_id)
            )
            user = result.scalar_one_or_none()

            if not user or not user.is_superuser or not user.is_active:
                request.session.clear()
                return RedirectResponse(request.url_for("admin:login"), status_code=302)

        return True


class UserAdmin(ModelView, model=User):
    """
    Admin view for User model.

    Allows viewing and editing user status fields.
    Creating and deleting users is disabled for safety.
    """

    # Display name in admin sidebar
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    # List view configuration
    column_list = [
        User.id,
        User.email,
        User.is_active,
        User.is_verified,
        User.is_superuser,
        User.created_at,
    ]

    # Searchable columns
    column_searchable_list = [User.email]

    # Sortable columns
    column_sortable_list = [
        User.email,
        User.is_active,
        User.is_verified,
        User.is_superuser,
        User.created_at,
    ]

    # Default sort
    column_default_sort = [(User.created_at, True)]  # Descending

    # Detail view - exclude sensitive and relationship fields
    # Relationships (user_data, tokens, refresh_tokens) cause lazy loading issues
    column_details_exclude_list = [
        User.hashed_password,
        User.user_data,
        User.tokens,
        User.refresh_tokens,
    ]

    # Form configuration - only allow editing status fields
    # (form_columns implicitly excludes all other fields including relationships)
    form_columns = [
        User.is_active,
        User.is_verified,
        User.is_superuser,
    ]

    # Disable create and delete for safety
    can_create = False
    can_delete = False
    can_edit = True
    can_view_details = True
    can_export = False

    # Pagination
    page_size = 20
    page_size_options = [20, 50, 100]

    def _stmt_by_identifier(self, identifier: str):
        """
        Override to properly handle UUID primary key.

        SQLAdmin has issues with fastapi-users UUID type detection.
        This method manually parses the UUID and creates the query.
        """
        pk = uuid.UUID(identifier)
        return select(User).where(User.id == pk)


def setup_admin(app):
    """
    Initialize and mount SQLAdmin to the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    authentication_backend = AdminAuth(secret_key=config.secret_key)

    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="FastAPI Auth Admin",
    )

    admin.add_view(UserAdmin)

    return admin
