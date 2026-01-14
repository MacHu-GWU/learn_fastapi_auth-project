# -*- coding: utf-8 -*-

"""
Authentication Routes.

Provides all authentication-related endpoints:
- fastapi-users routes (register, login, verify, reset-password, users)
- Custom routes (logout, refresh, change-password, firebase)
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_users.password import PasswordHelper
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.firebase import (
    FirebaseNotInitializedError,
    FirebaseTokenInvalidError,
    get_user_info_from_token,
    verify_firebase_token,
)
from ..auth.users import (
    auth_backend,
    current_active_user,
    fastapi_users,
    get_jwt_strategy,
    get_user_manager,
)
from ..models import User, UserData
from ..one.api import one
from ..ratelimit import limiter
from ..refresh_token import (
    create_refresh_token,
    get_refresh_token_cookie_settings,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    validate_refresh_token,
)
from ..schemas import (
    ChangePasswordRequest,
    FirebaseLoginRequest,
    FirebaseLoginResponse,
    MessageResponse,
    TokenRefreshResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter()


# =============================================================================
# fastapi-users Routes
# =============================================================================
# Register route
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)

# Login route
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"],
)

# Verification routes (request-verify, verify)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/api/auth",
    tags=["auth"],
)

# Password reset routes
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/auth",
    tags=["auth"],
)

# User management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/users",
    tags=["users"],
)


# =============================================================================
# Custom Authentication Routes
# =============================================================================
@router.post(
    "/api/auth/logout",
    response_model=MessageResponse,
    tags=["auth"],
)
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


@router.post(
    "/api/auth/refresh",
    response_model=TokenRefreshResponse,
    tags=["auth"],
)
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
    result = await session.execute(select(User).where(User.id == user_id))
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


@router.post(
    "/api/auth/logout-all",
    response_model=MessageResponse,
    tags=["auth"],
)
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


@router.post(
    "/api/auth/change-password",
    response_model=MessageResponse,
    tags=["auth"],
)
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
@router.post(
    "/api/auth/firebase",
    response_model=FirebaseLoginResponse,
    tags=["auth"],
)
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
    except FirebaseTokenInvalidError:
        raise HTTPException(
            status_code=401,
            detail="FIREBASE_TOKEN_INVALID",
        )

    firebase_uid = user_info.firebase_uid
    email = user_info.email

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

            # Hash the password
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
            print(f"Created new user {user.id} via Firebase ({user_info.provider})")

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
            "email": email,
        }
    )
    cookie_settings = get_refresh_token_cookie_settings(one.env.refresh_token_lifetime)
    response.set_cookie(value=refresh_token_str, **cookie_settings)

    return response
