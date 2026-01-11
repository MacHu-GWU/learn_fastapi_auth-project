# -*- coding: utf-8 -*-

"""
FastAPI Application Entry Point.

This module initializes the FastAPI application with all routes and configurations.
"""

from contextlib import asynccontextmanager

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
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
from .one.api import one
from .models import User, UserData
from .csrf import setup_csrf_protection
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
from .schemas import (
    ChangePasswordRequest,
    FirebaseLoginRequest,
    FirebaseLoginResponse,
    MessageResponse,
    TokenRefreshResponse,
    UserCreate,
    UserDataRead,
    UserDataUpdate,
    UserRead,
    UserUpdate,
)
from .auth.firebase import (
    init_firebase,
    verify_firebase_token,
    get_user_info_from_token,
    FirebaseTokenInvalidError,
    FirebaseNotInitializedError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - creates database tables on startup."""
    await one.create_db_and_tables()
    # Initialize Firebase if enabled
    if one.env.firebase_enabled:
        init_firebase()
    yield


app = FastAPI(
    title="FastAPI User Authentication",
    description="A SaaS authentication service with email verification",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Next.js frontend
# In development, Next.js runs on port 3000
# In production on Vercel, same-origin requests don't need CORS
# But we add the Vercel domain for API testing from other tools
import os

cors_origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

# Add production origins
if os.environ.get("VERCEL"):
    # On Vercel, add the production domain
    cors_origins.extend([
        "https://learn-fastapi-auth-project.vercel.app",
        "https://*.vercel.app",  # Preview deployments
    ])

# Allow additional origins from environment variable
extra_origins = os.environ.get("CORS_ORIGINS", "")
if extra_origins:
    cors_origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Allow cookies for refresh token
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup rate limiting
setup_rate_limiting(app)
app.add_middleware(SlowAPIMiddleware)

# Add path-based rate limiting for fastapi-users routes
# This middleware must be added BEFORE SlowAPIMiddleware takes effect
# Rate limits are configured in one.env.py and can be overridden via environment variables
path_rate_limits = {
    "/api/auth/login": one.env.rate_limit_login,  # Login: 5/minute (prevent brute force)
    "/api/auth/register": one.env.rate_limit_register,  # Register: 10/hour (prevent spam)
    "/api/auth/forgot-password": one.env.rate_limit_forgot_password,  # Reset: 3/hour
}
app.middleware("http")(create_path_rate_limit_middleware(path_rate_limits))

# Setup CSRF protection
# Note: API endpoints using Bearer token auth are exempt from CSRF checks
# because they don't use cookies for authentication
setup_csrf_protection(app, one.env.secret_key)


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
                    import uuid

                    # Determine token lifetime based on remember_me
                    token_lifetime = (
                        one.env.remember_me_refresh_token_lifetime
                        if remember_me
                        else one.env.refresh_token_lifetime
                    )

                    async with one.async_session_maker() as session:
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
@limiter.limit(one.env.rate_limit_default)
async def logout(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(one.get_async_session),
):
    """
    Logout user by revoking their refresh token.

    Clears the refresh token cookie and removes it from the database.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get(one.env.refresh_token_cookie_name)

    if refresh_token:
        await revoke_refresh_token(session, refresh_token)

    # Create response that clears the refresh token cookie
    response = JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=200,
    )
    response.delete_cookie(
        key=one.env.refresh_token_cookie_name,
        path="/api/auth",
    )
    return response


@app.post("/api/auth/refresh", response_model=TokenRefreshResponse, tags=["auth"])
@limiter.limit(one.env.rate_limit_default)
async def refresh_access_token(
    request: Request,
    session: AsyncSession = Depends(one.get_async_session),
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
    refresh_token = request.cookies.get(one.env.refresh_token_cookie_name)

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
@limiter.limit(one.env.rate_limit_login)
async def logout_all_devices(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(one.get_async_session),
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
        key=one.env.refresh_token_cookie_name,
        path="/api/auth",
    )
    return response


@app.post("/api/auth/change-password", response_model=MessageResponse, tags=["auth"])
@limiter.limit(one.env.rate_limit_login)
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
# Firebase OAuth Login
# =============================================================================
@app.post("/api/auth/firebase", response_model=FirebaseLoginResponse, tags=["auth"])
@limiter.limit(one.env.rate_limit_login)
async def firebase_login(
    request: Request,
    data: FirebaseLoginRequest,
    session: AsyncSession = Depends(one.get_async_session),
):
    """
    Login or register using Firebase Authentication (Google, Apple, etc.).

    This endpoint:
    1. Verifies the Firebase ID token
    2. Finds or creates a user based on Firebase UID or email
    3. Returns our own JWT access token + sets refresh token cookie

    The frontend should:
    1. Use Firebase JS SDK to sign in with Google/Apple
    2. Get the ID token from Firebase
    3. Send the ID token to this endpoint
    """
    import secrets
    from .auth.users import get_jwt_strategy

    # Check if Firebase is enabled
    if not one.env.firebase_enabled:
        raise HTTPException(
            status_code=503,
            detail="FIREBASE_AUTH_DISABLED",
        )

    # Verify Firebase token
    try:
        decoded_token = verify_firebase_token(data.id_token)
        user_info = get_user_info_from_token(decoded_token)
    except FirebaseNotInitializedError:
        raise HTTPException(
            status_code=503,
            detail="FIREBASE_NOT_INITIALIZED",
        )
    except FirebaseTokenInvalidError as e:
        raise HTTPException(
            status_code=401,
            detail="FIREBASE_TOKEN_INVALID",
        )

    firebase_uid = user_info["firebase_uid"]
    email = user_info["email"]

    if not email:
        raise HTTPException(
            status_code=400,
            detail="FIREBASE_EMAIL_REQUIRED",
        )

    is_new_user = False

    # Try to find existing user by firebase_uid
    result = await session.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Try to find by email (user may have registered with password first)
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is not None:
            # Link Firebase UID to existing user
            user.firebase_uid = firebase_uid
            session.add(user)
            await session.commit()
            print(f"Linked Firebase UID {firebase_uid} to existing user {user.id}")
        else:
            # Create new user
            # Generate a random password (user won't use it, they'll use OAuth)
            random_password = secrets.token_urlsafe(32)
            from .auth.users import UserManager

            # Hash the password
            from fastapi_users.password import PasswordHelper

            password_helper = PasswordHelper()
            hashed_password = password_helper.hash(random_password)

            user = User(
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=True,  # Firebase verified the email
                is_superuser=False,
                firebase_uid=firebase_uid,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Create UserData for the new user
            user_data = UserData(user_id=user.id, text_value="")
            session.add(user_data)
            await session.commit()

            is_new_user = True
            print(f"Created new user {user.id} via Firebase ({user_info['provider']})")

    # Generate our own JWT access token
    jwt_strategy = get_jwt_strategy()
    access_token = await jwt_strategy.write_token(user)

    # Create refresh token
    refresh_token_str = await create_refresh_token(
        session, user.id, one.env.refresh_token_lifetime
    )

    # Build response with refresh token cookie
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "is_new_user": is_new_user,
        }
    )
    cookie_settings = get_refresh_token_cookie_settings(one.env.refresh_token_lifetime)
    response.set_cookie(value=refresh_token_str, **cookie_settings)

    return response


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
        url=f"{one.env.final_frontend_url}/signin?verified=pending&token={token}",
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
        url=f"{one.env.final_frontend_url}/reset-password?token={token}",
        status_code=status.HTTP_302_FOUND,
    )


# =============================================================================
# User Data API Routes
# =============================================================================
@app.get("/api/user-data", response_model=UserDataRead, tags=["user-data"])
@limiter.limit(one.env.rate_limit_default)
async def get_user_data(
    request: Request,
    user: User = Depends(current_verified_user),
    session: AsyncSession = Depends(one.get_async_session),
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
@limiter.limit(one.env.rate_limit_default)
async def update_user_data(
    request: Request,
    data: UserDataUpdate,
    user: User = Depends(current_verified_user),
    session: AsyncSession = Depends(one.get_async_session),
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


