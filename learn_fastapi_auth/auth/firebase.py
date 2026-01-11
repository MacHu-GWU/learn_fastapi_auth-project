# -*- coding: utf-8 -*-

"""
Firebase Authentication integration.

Handles Firebase ID Token verification and user association for OAuth logins
(Google, Apple, etc.).
"""

import os
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from learn_fastapi_auth.one.api import one


# Firebase app instance (initialized lazily)
_firebase_app: Optional[firebase_admin.App] = None


class FirebaseAuthError(Exception):
    """Base exception for Firebase authentication errors."""

    pass


class FirebaseTokenInvalidError(FirebaseAuthError):
    """Raised when the Firebase token is invalid or expired."""

    pass


class FirebaseNotInitializedError(FirebaseAuthError):
    """Raised when Firebase is not properly initialized."""

    pass


def init_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.

    Returns:
        True if initialization successful, False otherwise.

    Note:
        This function is idempotent - calling it multiple times is safe.
    """
    global _firebase_app

    if _firebase_app is not None:
        return True

    if not one.env.firebase_enabled:
        print("Firebase authentication is disabled.")
        return False

    # Resolve service account path relative to project root
    service_account_path = Path(one.env.firebase_service_account_path)
    if not service_account_path.is_absolute():
        # Try relative to project root (parent of learn_fastapi_auth package)
        project_root = Path(__file__).parent.parent.parent
        service_account_path = project_root / one.env.firebase_service_account_path

    if not service_account_path.exists():
        print(f"Firebase service account file not found: {service_account_path}")
        return False

    try:
        cred = credentials.Certificate(str(service_account_path))
        _firebase_app = firebase_admin.initialize_app(cred)
        print(f"Firebase initialized successfully for project: {cred.project_id}")
        return True
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return False


def is_firebase_initialized() -> bool:
    """Check if Firebase is initialized."""
    return _firebase_app is not None


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
    if not is_firebase_initialized():
        raise FirebaseNotInitializedError(
            "Firebase is not initialized. Call init_firebase() first."
        )

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise FirebaseTokenInvalidError("Firebase token has expired.")
    except auth.InvalidIdTokenError:
        raise FirebaseTokenInvalidError("Firebase token is invalid.")
    except auth.RevokedIdTokenError:
        raise FirebaseTokenInvalidError("Firebase token has been revoked.")
    except FirebaseError as e:
        raise FirebaseTokenInvalidError(f"Firebase authentication error: {e}")


def get_user_info_from_token(decoded_token: dict) -> dict:
    """
    Extract user information from a decoded Firebase token.

    Args:
        decoded_token: The decoded Firebase token from verify_firebase_token().

    Returns:
        Dictionary with normalized user info:
        - firebase_uid: Firebase user ID
        - email: User's email address
        - email_verified: Whether email is verified by the provider
        - name: User's display name (or None)
        - picture: Profile picture URL (or None)
        - provider: Sign-in provider (google.com, apple.com, etc.)
    """
    # Get the sign-in provider from Firebase claims
    firebase_claims = decoded_token.get("firebase", {})
    provider = firebase_claims.get("sign_in_provider", "unknown")

    return {
        "firebase_uid": decoded_token.get("uid"),
        "email": decoded_token.get("email"),
        "email_verified": decoded_token.get("email_verified", False),
        "name": decoded_token.get("name"),
        "picture": decoded_token.get("picture"),
        "provider": provider,
    }
