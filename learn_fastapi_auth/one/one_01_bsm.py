# -*- coding: utf-8 -*-

"""
Boto session management mixin for AWS service access and credential handling.
"""

import typing as T
from functools import cached_property

from ..boto_ses import BotoSesEnum

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneBsmMixin:  # pragma: no cover
    """
    Mixin providing lazy-loaded boto session management and AWS console access.
    """
    @cached_property
    def bsm_enum(self: "One") -> BotoSesEnum:
        """
        Create and cache the boto session enumeration for multi-environment access.
        """
        return BotoSesEnum.new()

    @cached_property
    def bsm_devops(self: "One"):
        """
        Access DevOps environment boto session manager for cross-account operations.
        """
        return self.bsm_enum.bsm_devops

    @cached_property
    def aws_console_devops(self):
        """
        Access DevOps environment AWS console URL generator.
        """
        return self.bsm_enum.aws_console_devops

    @cached_property
    def bsm(self: "One"):
        """
        Access current environment boto session manager with automatic detection.
        """
        return self.bsm_enum.bsm

    @cached_property
    def aws_console(self):
        """
        Access current environment AWS console URL generator.
        """
        return self.bsm_enum.aws_console
