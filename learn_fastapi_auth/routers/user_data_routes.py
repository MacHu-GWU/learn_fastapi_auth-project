# -*- coding: utf-8 -*-

"""
User Data Routes.

Provides CRUD endpoints for user-specific data.
All endpoints require verified user authentication.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.users import current_verified_user
from ..models import User, UserData
from ..one.api import one
from ..ratelimit import limiter
from ..schemas import UserDataRead, UserDataUpdate

router = APIRouter(prefix="/api/user-data", tags=["user-data"])


@router.get(
    "",
    response_model=UserDataRead,
)
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


@router.put(
    "",
    response_model=UserDataRead,
)
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
