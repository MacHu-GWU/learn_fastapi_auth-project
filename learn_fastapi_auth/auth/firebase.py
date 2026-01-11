# -*- coding: utf-8 -*-

"""
Firebase Authentication integration.

This module handles Firebase ID Token verification for OAuth logins (Google, Apple, etc.).

Firebase Authentication Flow
============================

Firebase acts as a middleman between your app and OAuth providers (Google, Apple, etc.)::

    +-----------+     +----------+     +----------------+     +-----------+
    |  Frontend | --> | Firebase | --> | OAuth Provider | --> |  Backend  |
    |  (App)    |     |  Auth    |     | (Google/Apple) |     | (FastAPI) |
    +-----------+     +----------+     +----------------+     +-----------+
          |                |                   |                    |
          |  1. User clicks "Sign in with Google"                   |
          |--------------->|                   |                    |
          |                |  2. Redirect to   |                    |
          |                |     Google login  |                    |
          |                |------------------>|                    |
          |                |                   |                    |
          |                |  3. User logs in, |                    |
          |                |     Google returns|                    |
          |                |     auth code     |                    |
          |                |<------------------|                    |
          |                |                   |                    |
          |  4. Firebase returns ID Token (JWT)                     |
          |<---------------|                   |                    |
          |                                                         |
          |  5. Frontend sends ID Token to your backend             |
          |-------------------------------------------------------->|
          |                                                         |
          |                    6. Backend verifies token with       |
          |                       Firebase Admin SDK                |
          |                       (this module!)                    |
          |                                                         |
          |  7. Backend creates/finds local user, returns your JWT  |
          |<--------------------------------------------------------|

Why Firebase?
=============

Without Firebase, you'd need to:

1. Register your app with each OAuth provider (Google, Apple, Facebook, etc.)
2. Implement OAuth flow for each provider separately
3. Handle each provider's token format and verification

With Firebase:

1. Register once with Firebase
2. Firebase handles all OAuth providers uniformly
3. You always verify the same Firebase ID Token format

Key Concepts
============

Firebase ID Token
    A JWT issued by Firebase after successful OAuth login.
    Contains user info (email, name, picture) and is signed by Firebase.
    Your backend verifies this token to trust the user's identity.

Firebase UID
    A unique identifier assigned by Firebase to each user.
    Different from the OAuth provider's user ID.
    Use this to link Firebase users to your local User model.

Service Account
    A JSON credential file that proves your backend is authorized
    to use Firebase Admin SDK. Downloaded from Firebase Console.

Usage Example
=============

::

    # In your login endpoint
    @router.post("/auth/firebase")
    async def firebase_login(id_token: str):
        # 1. Verify the token is valid and from Firebase
        decoded = verify_firebase_token(id_token)

        # 2. Extract user info
        user_info = get_user_info_from_token(decoded)

        # 3. Find or create local user
        user = await find_or_create_user(
            firebase_uid=user_info.firebase_uid,
            email=user_info.email
        )

        # 4. Return your own JWT
        return {"access_token": create_jwt(user)}
"""

import dataclasses

from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from ..one.api import one


class FirebaseAuthError(Exception):
    """Base exception for Firebase authentication errors."""


class FirebaseTokenInvalidError(FirebaseAuthError):
    """
    Raised when the Firebase token is invalid or expired.

    Common causes:

    - Token expired (default lifetime is 1 hour)
    - Token was revoked (user signed out on all devices)
    - Token signature is invalid (tampered or fake token)
    - Token is malformed
    """


class FirebaseNotInitializedError(FirebaseAuthError):
    """
    Raised when Firebase is not properly initialized.

    Fix: Call ``one.init_firebase()`` during app startup (in lifespan handler).
    """


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID Token and return the decoded claims.

    This is the core security function. It:

    1. Checks the token signature using Firebase's public keys
    2. Verifies the token hasn't expired
    3. Verifies the token was issued for your Firebase project
    4. Returns the decoded user claims if everything checks out

    Args:
        id_token: The Firebase ID token from the frontend.
            This is a JWT string that looks like: "eyJhbGciOiJSUzI1NiIs..."

    Returns:
        Decoded token claims (dict) containing:

        - ``uid``: Firebase user ID (use this to identify users)
        - ``email``: User's email address
        - ``email_verified``: Whether email is verified by the provider
        - ``name``: User's display name (may be None for Apple)
        - ``picture``: Profile picture URL (may be None for Apple)
        - ``firebase.sign_in_provider``: "google.com", "apple.com", etc.

    Raises:
        FirebaseNotInitializedError: If Firebase Admin SDK is not initialized.
        FirebaseTokenInvalidError: If the token is invalid, expired, or revoked.

    Example::

        try:
            claims = verify_firebase_token(id_token)
            firebase_uid = claims["uid"]
            email = claims["email"]
        except FirebaseTokenInvalidError:
            raise HTTPException(401, "Invalid Firebase token")
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
    """
    User information extracted from a Firebase token.

    This dataclass normalizes the raw Firebase token claims into a clean structure.

    :param firebase_uid: Unique Firebase user ID. Use this to link to your local User model.
    :param email: User's email. Usually present for Google, may be hidden for Apple.
    :param email_verified: True if the OAuth provider verified the email.
    :param name: Display name. Google provides this, Apple may not.
    :param picture: Profile picture URL. Google provides this, Apple does not.
    :param provider: OAuth provider identifier ("google.com", "apple.com", etc.).
    """

    firebase_uid: str
    email: str | None
    email_verified: bool
    name: str | None
    picture: str | None
    provider: str


def get_user_info_from_token(decoded_token: dict) -> FirebaseUserInfo:
    """
    Extract user information from a decoded Firebase token.

    This is a convenience function that extracts and normalizes
    user information from the raw Firebase token claims.

    Args:
        decoded_token: The decoded Firebase token from :func:`verify_firebase_token`.

    Returns:
        :class:`FirebaseUserInfo` with normalized user data.

    Note:
        Different OAuth providers include different information:

        - **Google**: Provides email, name, and picture
        - **Apple**: May hide email (user can choose), rarely provides name/picture

        Always handle None values for optional fields.

    Example::

        decoded = verify_firebase_token(id_token)
        user_info = get_user_info_from_token(decoded)

        # Safe to use
        print(f"Firebase UID: {user_info.firebase_uid}")
        print(f"Provider: {user_info.provider}")

        # May be None
        if user_info.email:
            print(f"Email: {user_info.email}")
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
