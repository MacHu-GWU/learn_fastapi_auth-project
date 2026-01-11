# -*- coding: utf-8 -*-

"""
Application factory for external use.

This module provides backward compatibility for code that imports
create_app from this location.
"""

from .core import create_app

__all__ = ["create_app"]
