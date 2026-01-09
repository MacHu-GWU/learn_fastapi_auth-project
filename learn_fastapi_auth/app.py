# -*- coding: utf-8 -*-

"""
FastAPI Application Entry Point.

This module initializes the FastAPI application with all routes and configurations.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth.users import (
    auth_backend,
    current_active_user,
    current_verified_user,
    delete_token,
    fastapi_users,
    get_user_manager,
)
from .config import config
from .database import create_db_and_tables, get_async_session
from .models import User, UserData
from .paths import dir_static, dir_templates
from .csrf import get_csrf_token, setup_csrf_protection
from .ratelimit import (
    create_path_rate_limit_middleware,
    limiter,
    rate_limit_exceeded_handler,
    setup_rate_limiting,
)
from .routers import pages_router
from .schemas import (
    ChangePasswordRequest,
    MessageResponse,
    UserCreate,
    UserDataRead,
    UserDataUpdate,
    UserRead,
    UserUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - creates database tables on startup."""
    await create_db_and_tables()
    yield


app = FastAPI(
    title="FastAPI User Authentication",
    description="A SaaS authentication service with email verification",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup rate limiting
setup_rate_limiting(app)
app.add_middleware(SlowAPIMiddleware)

# Add path-based rate limiting for fastapi-users routes
# This middleware must be added BEFORE SlowAPIMiddleware takes effect
# Rate limits are configured in config.py and can be overridden via environment variables
path_rate_limits = {
    "/api/auth/login": config.rate_limit_login,  # Login: 5/minute (prevent brute force)
    "/api/auth/register": config.rate_limit_register,  # Register: 10/hour (prevent spam)
    "/api/auth/forgot-password": config.rate_limit_forgot_password,  # Reset: 3/hour
}
app.middleware("http")(create_path_rate_limit_middleware(path_rate_limits))

# Setup CSRF protection
# Note: API endpoints using Bearer token auth are exempt from CSRF checks
# because they don't use cookies for authentication
setup_csrf_protection(app, config.secret_key)

# Mount static files
app.mount("/static", StaticFiles(directory=str(dir_static)), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory=str(dir_templates))

# Add CSRF token function to Jinja2 globals for use in templates
# Usage in templates: {{ get_csrf_token(request) }}
templates.env.globals["get_csrf_token"] = get_csrf_token

# Include page router (HTML pages)
app.include_router(pages_router)


# =============================================================================
# Authentication Routes (from fastapi-users)
# =============================================================================
# Register route
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)

# Login route
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"],
)

# Verification routes (request-verify, verify)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/api/auth",
    tags=["auth"],
)

# Password reset routes
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/auth",
    tags=["auth"],
)

# User management routes
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/users",
    tags=["users"],
)


# =============================================================================
# Custom Authentication Routes
# =============================================================================
@app.post("/api/auth/logout", response_model=MessageResponse, tags=["auth"])
@limiter.limit(config.rate_limit_default)
async def logout(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Logout user by invalidating their token."""
    # Note: In a production system, you would get the token from the request
    # and delete it from the database. For simplicity, we just return success.
    return MessageResponse(message="Successfully logged out")


@app.post("/api/auth/change-password", response_model=MessageResponse, tags=["auth"])
@limiter.limit(config.rate_limit_login)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    user: User = Depends(current_active_user),
    user_manager=Depends(get_user_manager),
):
    """
    Change password for logged-in user.

    Requires current password verification before updating to new password.
    """
    # Verify current password
    verified, _ = user_manager.password_helper.verify_and_update(
        data.current_password, user.hashed_password
    )
    if not verified:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail="CHANGE_PASSWORD_INVALID_CURRENT",
        )

    # Update to new password
    hashed_password = user_manager.password_helper.hash(data.new_password)
    user.hashed_password = hashed_password

    session = user_manager.user_db.session
    session.add(user)
    await session.commit()

    return MessageResponse(message="Password changed successfully")


# =============================================================================
# Email Verification Page Route
# =============================================================================
@app.get("/auth/verify-email", tags=["pages"])
async def verify_email_page(
    token: str = Query(..., description="Verification token"),
):
    """
    Handle email verification link.

    This route is accessed when a user clicks the verification link in their email.
    It verifies the token and redirects to the appropriate page.
    """
    # The actual verification is handled by fastapi-users POST /api/auth/verify
    # This page should redirect to a frontend page that will call the API
    return RedirectResponse(
        url=f"{config.frontend_url}/signin?verified=pending&token={token}",
        status_code=status.HTTP_302_FOUND,
    )


# =============================================================================
# Password Reset Page Route
# =============================================================================
@app.get("/auth/reset-password", tags=["pages"])
async def reset_password_redirect(
    token: str = Query(..., description="Password reset token"),
):
    """
    Handle password reset link from email.

    This route is accessed when a user clicks the reset link in their email.
    It redirects to the reset password page with the token.
    """
    return RedirectResponse(
        url=f"{config.frontend_url}/reset-password?token={token}",
        status_code=status.HTTP_302_FOUND,
    )


# =============================================================================
# User Data API Routes
# =============================================================================
@app.get("/api/user-data", response_model=UserDataRead, tags=["user-data"])
@limiter.limit(config.rate_limit_default)
async def get_user_data(
    request: Request,
    user: User = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get current user's data."""
    result = await session.execute(select(UserData).where(UserData.user_id == user.id))
    user_data = result.scalar_one_or_none()

    if not user_data:
        # Create user_data if it doesn't exist
        user_data = UserData(user_id=user.id, text_value="")
        session.add(user_data)
        await session.commit()
        await session.refresh(user_data)

    return user_data


@app.put("/api/user-data", response_model=UserDataRead, tags=["user-data"])
@limiter.limit(config.rate_limit_default)
async def update_user_data(
    request: Request,
    data: UserDataUpdate,
    user: User = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update current user's data."""
    result = await session.execute(select(UserData).where(UserData.user_id == user.id))
    user_data = result.scalar_one_or_none()

    if not user_data:
        # Create user_data if it doesn't exist
        user_data = UserData(user_id=user.id, text_value=data.text_value)
        session.add(user_data)
    else:
        user_data.text_value = data.text_value

    await session.commit()
    await session.refresh(user_data)

    return user_data


# =============================================================================
# Health Check
# =============================================================================
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


