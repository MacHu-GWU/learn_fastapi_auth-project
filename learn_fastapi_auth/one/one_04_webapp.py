# -*- coding: utf-8 -*-

"""
Firebase Admin SDK initialization.

This mixin manages the Firebase Admin SDK lifecycle for the One singleton.

Firebase Admin SDK vs Firebase Client SDK
=========================================

There are two Firebase SDKs - don't confuse them:

Firebase Client SDK (frontend)
    Used in mobile apps and web frontends.
    Handles user sign-in UI and returns ID Tokens.
    npm package: ``firebase``

Firebase Admin SDK (backend) - THIS MODULE
    Used in your backend server.
    Verifies ID Tokens from the client SDK.
    Python package: ``firebase-admin``

Why Initialize Firebase Admin SDK?
==================================

The Admin SDK needs initialization to:

1. Load your service account credentials (proves your backend is authorized)
2. Know which Firebase project to verify tokens against
3. Cache Firebase's public keys for token signature verification

Service Account Setup
=====================

1. Go to Firebase Console > Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save the JSON file securely (never commit to git!)
4. Set the path in your config: ``FIREBASE_SERVICE_ACCOUNT_PATH``

The JSON file looks like::

    {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "...",
        "private_key": "-----BEGIN PRIVATE KEY-----...",
        "client_email": "firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com",
        ...
    }
"""

import typing as T

import firebase_admin
from firebase_admin import credentials

from ..logger import logger

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneWebAppMixin:  # pragma: no cover
    """
    Mixin providing Firebase Admin SDK initialization.

    The Firebase app instance is stored as ``one.firebase_app``.
    """

    @property
    def is_firebase_initialized(self: "One") -> bool:
        """
        Check if Firebase Admin SDK is initialized.

        Returns:
            True if ``one.firebase_app`` is set, False otherwise.
        """
        return self.firebase_app is not None

    def init_firebase(self: "One") -> bool:
        """
        Initialize Firebase Admin SDK.

        This method:

        1. Checks if already initialized (returns True immediately)
        2. Checks if Firebase is enabled in config (returns False if disabled)
        3. Loads service account credentials from the configured path
        4. Initializes the Firebase Admin SDK

        Returns:
            True if initialization successful or already initialized.
            False if Firebase is disabled or initialization failed.

        Note:
            This function is idempotent - calling it multiple times is safe.
            The second call will just return True without re-initializing.

        Example::

            # In your app lifespan handler
            @asynccontextmanager
            async def lifespan(app: FastAPI):
                one.init_firebase()  # Initialize on startup
                yield

        Raises:
            No exceptions - errors are logged and False is returned.
        """
        if self.firebase_app is not None:
            return True

        if not self.env.firebase_enabled:
            logger.info("Firebase authentication is disabled.")
            return False

        try:
            cred = credentials.Certificate(self.firebase_service_account_cert)
            self.firebase_app = firebase_admin.initialize_app(cred)
            logger.info(
                f"Firebase initialized successfully for project: {cred.project_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            return False
