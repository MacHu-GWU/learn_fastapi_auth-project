# -*- coding: utf-8 -*-

"""
Main configuration module providing centralized environment and application settings.

This module contains the core configuration classes that serve as the foundation for all
application configuration management, integrating environment-specific settings with
multi-environment detection and providing type-safe configuration access patterns.
"""

import dataclasses
from functools import cached_property

import aws_config.api as aws_config
from s3pathlib import S3Path

from ..env import EnvNameEnum, detect_current_env

# You may have a long list of config field definition
# put them in different module and use Mixin class
from .config_01_db import DbMixin


class Env(
    aws_config.BaseEnv,
    DbMixin,
):
    """
    Environment-specific configuration container with Lambda function integration.

    Combines base environment settings with Lambda function and deployment configurations
    using mixin classes to provide a comprehensive configuration interface for each
    deployment environment while maintaining clear separation of concerns.
    """
    # Database
    db_host: str | None = dataclasses.field(default=None)
    db_user: str | None = dataclasses.field(default=None)
    db_pass: str | None = dataclasses.field(default=None)
    db_name: str | None = dataclasses.field(default=None)

    # JWT
    secret_key: str | None = dataclasses.field(default=None)

    # SMTP Email
    smtp_host: str | None = dataclasses.field(default=None)
    smtp_port: int | None = dataclasses.field(default=None)
    smtp_tls: bool | None = dataclasses.field(default=None)
    smtp_user: str | None = dataclasses.field(default=None)
    smtp_password: str | None = dataclasses.field(default=None)
    smtp_from: str | None = dataclasses.field(default=None)
    smtp_from_name: str | None = dataclasses.field(default=None)

    # Application
    frontend_url: str | None = dataclasses.field(default=None)
    verification_token_lifetime: int | None = dataclasses.field(default=None)
    reset_password_token_lifetime: int | None = dataclasses.field(default=None)
    access_token_lifetime: int | None = dataclasses.field(default=None)
    refresh_token_lifetime: int | None = dataclasses.field(default=None)
    remember_me_refresh_token_lifetime: int | None = dataclasses.field(default=None)

    # Refresh Token Cookie
    refresh_token_cookie_name: str | None = dataclasses.field(default=None)
    refresh_token_cookie_secure: bool | None = dataclasses.field(default=None)
    refresh_token_cookie_samesite: str | None = dataclasses.field(default=None)

    # Rate Limiting
    rate_limit_login: str | None = dataclasses.field(default=None)
    rate_limit_register: str | None = dataclasses.field(default=None)
    rate_limit_forgot_password: str | None = dataclasses.field(default=None)
    rate_limit_default: str | None = dataclasses.field(default=None)

    # CSRF Protection
    csrf_cookie_name: str | None = dataclasses.field(default=None)
    csrf_cookie_secure: bool | None = dataclasses.field(default=None)
    csrf_cookie_samesite: str | None = dataclasses.field(default=None)

    # Firebase Authentication
    firebase_service_account_cert: dict | None = dataclasses.field(default=None)
    firebase_enabled: bool | None = dataclasses.field(default=None)

    @property
    def s3dir_source(self: "Env") -> S3Path:
        return self.s3dir_env_data.joinpath("source").to_dir()

    @property
    def s3dir_target(self: "Env") -> S3Path:
        return self.s3dir_env_data.joinpath("target").to_dir()


@dataclasses.dataclass
class Config(
    aws_config.BaseConfig[Env, EnvNameEnum],
):
    """
    Main configuration class providing environment-aware configuration management.

    Extends the base configuration to provide type-safe access to environment-specific
    configurations with automatic environment detection and cached property access
    for efficient configuration loading and cross-environment operations.
    """
    @classmethod
    def get_current_env(cls) -> str:  # pragma: no cover
        return detect_current_env()

    @cached_property
    def devops(self) -> Env:  # pragma: no cover
        return self.get_env(env_name=EnvNameEnum.devops.value)

    @cached_property
    def dev(self):  # pragma: no cover
        return self.get_env(env_name=EnvNameEnum.dev.value)

    @cached_property
    def tst(self) -> Env:  # pragma: no cover
        return self.get_env(env_name=EnvNameEnum.tst.value)

    @cached_property
    def prd(self) -> Env:  # pragma: no cover
        return self.get_env(env_name=EnvNameEnum.prd.value)

    @cached_property
    def env(self) -> Env:
        return self.get_env(env_name=self.get_current_env())
