# -*- coding: utf-8 -*-

"""
Database connection and session management.

Provides async SQLAlchemy engine, session factory, and database initialization utilities.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass
