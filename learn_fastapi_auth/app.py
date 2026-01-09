# -*- coding: utf-8 -*-

"""
FastAPI Application Entry Point.

This module initializes the FastAPI application with all routes and configurations.
"""

from contextlib import asynccontextmanager

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
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
from .refresh_token import (
    create_refresh_token,
    get_refresh_token_cookie_settings,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    validate_refresh_token,
)
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
    TokenRefreshResponse,
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


# =============================================================================
# Login Middleware - Sets Refresh Token Cookie After Successful Login
# =============================================================================
@app.middleware("http")
async def add_refresh_token_on_login(request: Request, call_next):
    """
    Middleware to add refresh token cookie after successful login.

    This intercepts responses from /api/auth/login and adds a refresh token
    cookie for the token refresh mechanism.

    Supports "Remember Me" functionality:
    - If remember_me=true: refresh token lasts 30 days
    - If remember_me=false (default): refresh token lasts 7 days
    """
    import json
    import jwt

    # Check if this is a login request and extract remember_me before processing
    remember_me = False
    if request.url.path == "/api/auth/login" and request.method == "POST":
        # Read and cache request body to extract remember_me
        body_bytes = await request.body()

        # Parse form data to get remember_me parameter
        try:
            from urllib.parse import parse_qs
            form_data = parse_qs(body_bytes.decode())
            remember_me_values = form_data.get("remember_me", ["false"])
            remember_me = remember_me_values[0].lower() == "true"
        except Exception:
            pass

        # Store the body in request state so it can be re-read by the route
        # We need to replace the receive to allow body to be read again
        async def receive():
            return {"type": "http.request", "body": body_bytes}

        request = Request(request.scope, receive, request._send)

    response = await call_next(request)

    # Only process POST to login endpoint with successful response
    if (
        request.url.path == "/api/auth/login"
        and request.method == "POST"
        and response.status_code == 200
    ):
        # Read the response body to get the access token
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            # Parse the JSON response to get access_token
            data = json.loads(body.decode())
            access_token = data.get("access_token")

            if access_token:
                # Decode JWT to get user_id (without verification since we trust it)
                payload = jwt.decode(
                    access_token, options={"verify_signature": False}
                )
                user_id = payload.get("sub")

                if user_id:
                    # Create refresh token and store in database
                    from .database import async_session_maker
                    import uuid

                    # Determine token lifetime based on remember_me
                    token_lifetime = (
                        config.remember_me_refresh_token_lifetime
                        if remember_me
                        else config.refresh_token_lifetime
                    )

                    async with async_session_maker() as session:
                        refresh_token_str = await create_refresh_token(
                            session, uuid.UUID(user_id), token_lifetime
                        )

                    # Create new response with refresh token cookie
                    new_response = JSONResponse(
                        content=data,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                    cookie_settings = get_refresh_token_cookie_settings(token_lifetime)
                    new_response.set_cookie(
                        value=refresh_token_str,
                        **cookie_settings,
                    )
                    return new_response
        except Exception:
            # If anything fails, return original response
            pass

        # Return response with original body
        return JSONResponse(
            content=json.loads(body.decode()) if body else {},
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    return response


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
    """
    Logout user by revoking their refresh token.

    Clears the refresh token cookie and removes it from the database.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get(config.refresh_token_cookie_name)

    if refresh_token:
        await revoke_refresh_token(session, refresh_token)

    # Create response that clears the refresh token cookie
    response = JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=200,
    )
    response.delete_cookie(
        key=config.refresh_token_cookie_name,
        path="/api/auth",
    )
    return response


@app.post("/api/auth/refresh", response_model=TokenRefreshResponse, tags=["auth"])
@limiter.limit(config.rate_limit_default)
async def refresh_access_token(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a new access token using the refresh token.

    The refresh token is read from the HttpOnly cookie set during login.
    If the refresh token is valid and not expired, a new access token is issued.
    """
    from .auth.users import get_jwt_strategy, get_user_db
    from sqlalchemy import select
    from .models import User as UserModel

    # Get refresh token from cookie
    refresh_token = request.cookies.get(config.refresh_token_cookie_name)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="REFRESH_TOKEN_MISSING",
        )

    # Validate refresh token and get user_id
    user_id = await validate_refresh_token(session, refresh_token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="REFRESH_TOKEN_INVALID",
        )

    # Get user from database
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="USER_INACTIVE",
        )

    # Generate new access token
    jwt_strategy = get_jwt_strategy()
    access_token = await jwt_strategy.write_token(user)

    return TokenRefreshResponse(access_token=access_token)


@app.post("/api/auth/logout-all", response_model=MessageResponse, tags=["auth"])
@limiter.limit(config.rate_limit_login)
async def logout_all_devices(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Logout from all devices by revoking all refresh tokens.

    This invalidates all refresh tokens for the current user,
    effectively logging them out from all devices.
    """
    count = await revoke_all_user_refresh_tokens(session, user.id)

    # Create response that clears the refresh token cookie
    response = JSONResponse(
        content={
            "message": f"Successfully logged out from all devices. Revoked {count} sessions."
        },
        status_code=200,
    )
    response.delete_cookie(
        key=config.refresh_token_cookie_name,
        path="/api/auth",
    )
    return response


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


# =============================================================================
# Admin Dashboard (SQLAdmin)
# =============================================================================
from .admin import setup_admin

setup_admin(app)


