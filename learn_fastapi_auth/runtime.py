# -*- coding: utf-8 -*-

"""
Runtime environment detection for multi-context applications.

This module provides centralized runtime environment detection capabilities essential for
cloud-native applications that run across multiple execution contexts, enabling environment-aware
configuration and resource management without scattered conditional logic throughout the codebase.

.. seealso::

    :ref:`Understand-Runtime`
"""

import os
from functools import cached_property

import which_runtime.api as which_runtime


class Runtime(which_runtime.Runtime):
    """
    Runtime environment detection class for context-aware application behavior.

    Extends the base runtime detection to provide centralized identification of execution
    contexts including local development, CI/CD pipelines, and AWS compute environments,
    enabling consistent environment-aware configuration and resource access patterns.
    """

    @cached_property
    def is_vercel(self) -> bool:
        """Check if running in Vercel environment."""
        return "VERCEL" in os.environ

    @cached_property
    def is_local(self) -> bool:
        """
        Local runtime represents a standard development environment on a personal computer or
        local workstation. It is the default runtime when no specific cloud or CI/CD environment
        is detected.

        Detection occurs by checking if none of the other specific runtime environments are active.
        Users can also manually set the runtime using the USER_RUNTIME_NAME environment variable
        to explicitly indicate a local runtime.
        """
        is_local = super().is_local
        if is_local:
            if self.is_vercel:
                return False
        return is_local

    @cached_property
    def is_app_runtime_group(self) -> bool:
        return self.is_vercel

    @cached_property
    def current_runtime(self) -> str:  # pragma: no cover
        current_runtime = super().current_runtime
        if current_runtime == which_runtime.RunTimeEnum.unknown:
            if self.is_vercel:
                return "vercel"
        return current_runtime


runtime = Runtime()
