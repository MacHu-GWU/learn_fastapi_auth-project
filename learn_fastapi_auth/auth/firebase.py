# -*- coding: utf-8 -*-

"""
Firebase Authentication integration.

Handles Firebase ID Token verification and user association for OAuth logins
(Google, Apple, etc.).
"""

import dataclasses

from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from ..one.api import one


class FirebaseAuthError(Exception):
    """Base exception for Firebase authentication errors."""


class FirebaseTokenInvalidError(FirebaseAuthError):
    """Raised when the Firebase token is invalid or expired."""


class FirebaseNotInitializedError(FirebaseAuthError):
    """Raised when Firebase is not properly initialized."""


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID Token and return the decoded claims.

    Args:
        id_token: The Firebase ID token from the frontend.

    Returns:
        Decoded token claims containing:
        - uid: Firebase user ID
        - email: User's email address
        - email_verified: Whether email is verified
        - name: User's display name (may be None)
        - picture: User's profile picture URL (may be None)
        - firebase.sign_in_provider: The sign-in provider (google.com, apple.com, etc.)

    Raises:
        FirebaseNotInitializedError: If Firebase is not initialized.
        FirebaseTokenInvalidError: If the token is invalid or expired.
    """
    if not one.is_firebase_initialized:
        raise FirebaseNotInitializedError(
            "Firebase is not initialized. Call one.init_firebase() first."
        )

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise FirebaseTokenInvalidError("Firebase token has expired.")
    except auth.RevokedIdTokenError:
        raise FirebaseTokenInvalidError("Firebase token has been revoked.")
    except auth.InvalidIdTokenError:
        raise FirebaseTokenInvalidError("Firebase token is invalid.")
    except FirebaseError as e:
        raise FirebaseTokenInvalidError(f"Firebase authentication error: {e}")


@dataclasses.dataclass
class FirebaseUserInfo:
    """User information extracted from a Firebase token."""

    firebase_uid: str
    email: str | None
    email_verified: bool
    name: str | None
    picture: str | None
    provider: str


def get_user_info_from_token(decoded_token: dict) -> FirebaseUserInfo:
    """
    Extract user information from a decoded Firebase token.

    Args:
        decoded_token: The decoded Firebase token from verify_firebase_token().

    Returns:
        FirebaseUserInfo with normalized user data.
    """
    firebase_claims = decoded_token.get("firebase", {})
    provider = firebase_claims.get("sign_in_provider", "unknown")

    return FirebaseUserInfo(
        firebase_uid=decoded_token.get("uid"),
        email=decoded_token.get("email"),
        email_verified=decoded_token.get("email_verified", False),
        name=decoded_token.get("name"),
        picture=decoded_token.get("picture"),
        provider=provider,
    )
