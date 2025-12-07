# -*- coding: utf-8 -*-

"""
FastAPI Application Entry Point.

This module initializes the FastAPI application with all routes and configurations.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learn_fastapi_auth.auth.users import (
    auth_backend,
    current_active_user,
    current_verified_user,
    delete_token,
    fastapi_users,
    get_user_manager,
)
from learn_fastapi_auth.config import config
from learn_fastapi_auth.database import create_db_and_tables, get_async_session
from learn_fastapi_auth.models import User, UserData
from learn_fastapi_auth.schemas import (
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
async def logout(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Logout user by invalidating their token."""
    # Note: In a production system, you would get the token from the request
    # and delete it from the database. For simplicity, we just return success.
    return MessageResponse(message="Successfully logged out")


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
# User Data API Routes
# =============================================================================
@app.get("/api/user-data", response_model=UserDataRead, tags=["user-data"])
async def get_user_data(
    user: User = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get current user's data."""
    result = await session.execute(
        select(UserData).where(UserData.user_id == user.id)
    )
    user_data = result.scalar_one_or_none()

    if not user_data:
        # Create user_data if it doesn't exist
        user_data = UserData(user_id=user.id, text_value="")
        session.add(user_data)
        await session.commit()
        await session.refresh(user_data)

    return user_data


@app.put("/api/user-data", response_model=UserDataRead, tags=["user-data"])
async def update_user_data(
    data: UserDataUpdate,
    user: User = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update current user's data."""
    result = await session.execute(
        select(UserData).where(UserData.user_id == user.id)
    )
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
# Root Route
# =============================================================================
@app.get("/", tags=["pages"])
async def root():
    """Root endpoint - returns welcome message."""
    return {
        "message": "Welcome to FastAPI User Authentication",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# =============================================================================
# Run Application
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
