# -*- coding: utf-8 -*-

"""
WebApp.
"""

import typing as T

import firebase_admin
from firebase_admin import credentials

from ..logger import logger

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneWebAppMixin:  # pragma: no cover
    """Mixin providing Firebase app singleton management."""

    @property
    def is_firebase_initialized(self: "One") -> bool:
        """Check if Firebase is initialized."""
        return self.firebase_app is not None

    def init_firebase(self: "One") -> bool:
        """
        Initialize Firebase Admin SDK.

        Returns:
            True if initialization successful, False otherwise.

        Note:
            This function is idempotent - calling it multiple times is safe.
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
