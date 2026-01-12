# -*- coding: utf-8 -*-

"""
Page Redirect Routes.

Handles email link redirects for verification and password reset.
These routes redirect users to the frontend with appropriate tokens.
"""

from fastapi import APIRouter, Query, status
from fastapi.responses import RedirectResponse

from ..one.api import one

router = APIRouter(
    prefix="/auth",
    tags=["pages"],
)


@router.get("/verify-email")
async def verify_email_page(
    token: str = Query(..., description="Verification token"),
):
    """
    Handle email verification link.

    This route is accessed when a user clicks the verification link in their email.
    It redirects to the frontend page that will call the API to verify the token.
    """
    return RedirectResponse(
        url=f"{one.env.final_frontend_url}/signin?verified=pending&token={token}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/reset-password")
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
