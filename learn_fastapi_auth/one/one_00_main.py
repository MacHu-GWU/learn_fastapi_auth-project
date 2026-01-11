# -*- coding: utf-8 -*-

"""
Core singleton class combining all mixin functionality for centralized resource access.

This module provides the main One class that aggregates all specialized mixin functionality
into a single entry point, enabling lazy-loaded access to configuration, AWS services,
DevOps operations, and documentation generation through a unified singleton interface.
"""

import dataclasses

import firebase_admin

try:
    from pywf_internal_proprietary.api import PyWf
except ImportError:  # pragma: no cover
    pass

from ..runtime import Runtime, runtime
from ..paths import path_enum

from .one_01_bsm import OneBsmMixin
from .one_02_config import OneConfigMixin
from .one_03_db import OneDbMixin
from .one_04_webapp import OneWebAppMixin
from .one_05_devops import OneDevOpsMixin
from .one_06_quick_links import OneQuickLinksMixin

@dataclasses.dataclass
class One(
    OneBsmMixin,
    OneConfigMixin,
    OneDbMixin,
    OneWebAppMixin,
    OneDevOpsMixin,
    OneQuickLinksMixin,
):  # pragma: no cover
    """
    Main singleton class providing unified access to all application resources and services.
    """
    runtime: Runtime = dataclasses.field(default=runtime)
    firebase_app: firebase_admin.App | None = dataclasses.field(default=None)

    @property
    def pywf(self) -> "PyWf":
        """
        Access Python project metadata and dependency information from pyproject.toml.
        """
        return PyWf.from_pyproject_toml(path_enum.path_pyproject_toml)


one = One()
