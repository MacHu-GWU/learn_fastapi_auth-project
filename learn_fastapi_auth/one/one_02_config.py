# -*- coding: utf-8 -*-

"""
Configuration management mixin with runtime-aware loading and deployment operations.

This module provides comprehensive configuration management with adaptive loading strategies
based on runtime context, supporting local JSON files for development, SSM Parameter Store
for CI/CD and production, with automated secret management and multi-environment deployment.
"""

import typing as T
import os
import json
from functools import cached_property

from configcraft.api import DEFAULTS
from aws_config.vendor.jsonutils import json_loads
from simple_aws_ssm_parameter_store.api import ParameterType

from .._version import __version__
from ..paths import path_enum
from ..logger import logger
from ..runtime import runtime
from ..env import EnvNameEnum, detect_current_env
from ..config.api import Env, Config

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneConfigMixin:
    """
    Mixin providing runtime-aware configuration loading and management operations.
    """

    @cached_property
    def config(self: "One") -> Config:
        """
        Load configuration with runtime-aware strategy (local files, SSM, or environment variables).
        """
        if runtime.is_local_runtime_group:
            # ensure that the config-secret.json file exists
            # I recommend to put it at the ${HOME}/.projects/${project_name}/config-secret.json
            # if the user haven't created it yet, this code block will print helper
            # message and generate a sample config-secret.json file for the user.
            if not path_enum.path_secret_config_json.exists():  # pragma: no cover
                print(
                    f"create the initial {path_enum.path_secret_config_json} "
                    f"file for config data, please update it!"
                )
                path_enum.path_secret_config_json.parent.mkdir(
                    parents=True, exist_ok=True
                )
                initial_config_secret_data = {
                    DEFAULTS: {},
                }
                for env_name in EnvNameEnum:
                    initial_config_secret_data[env_name] = {
                        "make sure secret config match your config object definition": "...",
                    }
                config_secret_content = json.dumps(initial_config_secret_data, indent=4)
                path_enum.path_secret_config_json.write_text(config_secret_content)

            # read non-sensitive config and sensitive config from local file system
            data, secret_data = Config.load_from_file(
                path_config_json=path_enum.path_config_json,
                path_secret_config_json=path_enum.path_secret_config_json,
            )
            return Config(
                data=data,
                secret_data=secret_data,
                EnvClass=Env,
                EnvNameEnumClass=EnvNameEnum,
                version=__version__,
            )
        elif runtime.is_ci_runtime_group:  # pragma: no cover
            # read non-sensitive config from local file system
            # and then figure out what is the parameter name
            config = Config(
                data=json_loads(path_enum.path_config_json.read_text()),
                secret_data=dict(),
                EnvClass=Env,
                EnvNameEnumClass=EnvNameEnum,
                version="not-applicable",
            )
            # read config from parameter store
            env_name = detect_current_env()
            if env_name == EnvNameEnum.devops.value:
                bsm = self.bsm_enum.bsm_devops
                parameter_name = config.parameter_name
            else:
                bsm = self.bsm_enum.get_env_bsm(env_name)
                parameter_name = config.env.parameter_name
            data, secret_data = Config.load_parameter(
                ssm_client=bsm.ssm_client,
                parameter_name=parameter_name,
                with_decryption=True,
            )
            return Config(
                data=data,
                secret_data=secret_data,
                EnvClass=Env,
                EnvNameEnumClass=EnvNameEnum,
                version=__version__,
            )
            # app runtime
        else:  # pragma: no cover
            # read the parameter name from environment variable
            parameter_name = os.environ["PARAMETER_NAME"]
            # read config from parameter store
            data, secret_data = Config.load_parameter(
                ssm_client=self.bsm.ssm_client,
                parameter_name=parameter_name,
                with_decryption=True,
            )
            return Config(
                data=data,
                secret_data=secret_data,
                EnvClass=Env,
                EnvNameEnumClass=EnvNameEnum,
                version=__version__,
            )

    @cached_property
    def env(self: "One") -> Env:
        """
        Access current environment configuration object with automatic environment detection.
        """
        return self.config.env

    def deploy_config(self: "One"):  # pragma: no cover
        """
        Deploy configuration parameters to SSM Parameter Store across all environments.
        """
        @logger.emoji_block(
            msg="Deploy '{env_name}' environment config",
            emoji="🚀",
        )
        def deploy_env_parameter(env_name: str | None):
            """
            .. note::

                - ssm_client is per environment bsm
                - s3_client is always devops bsm
            """
            if env_name is not None:
                env = self.config.get_env(env_name=env_name)
                result = self.config.deploy_env_parameter(
                    ssm_client=self.bsm_enum.get_env_bsm(env_name=env_name).ssm_client,
                    s3_client=self.bsm_enum.bsm_devops.s3_client,
                    s3dir_config=env.s3dir_config_artifacts,
                    env_name=env_name,
                    type=ParameterType.SECURE_STRING,
                )
            else:
                result = self.config.deploy_env_parameter(
                    ssm_client=self.bsm_enum.bsm_devops.ssm_client,
                    s3_client=self.bsm_enum.bsm_devops.s3_client,
                    s3dir_config=self.config.dev.s3dir_config_artifacts,
                    type=ParameterType.SECURE_STRING,
                )

            name = result.parameter_name
            version = result.version
            url = self.aws_console.ssm.get_parameter(name)
            action = "CREATE" if result.is_ssm_deployed else "SKIP"
            if env_name is None:
                env_name = "devops"
            msg = (
                f"{action} ssm parameter in {env_name = }, "
                f"latest Parameter {name = }, {version = }, {url = }"
            )
            logger.info(msg)

            action = "CREATE" if result.is_s3_deployed else "SKIP"
            s3dir_config = result.s3dir_config
            url = s3dir_config.console_url
            msg = (
                f"{action} S3 config artifacts in {env_name = }, "
                f"{s3dir_config.uri = }, {url = }"
            )
            logger.info(msg)

        deploy_env_parameter(env_name=None)
        deploy_env_parameter(env_name=EnvNameEnum.dev.value)
        deploy_env_parameter(env_name=EnvNameEnum.tst.value)
        deploy_env_parameter(env_name=EnvNameEnum.prd.value)

    def delete_config(self: "One"):  # pragma: no cover
        """
        Delete configuration parameters from SSM Parameter Store across all environments.
        """
        @logger.emoji_block(
            msg="Delete '{env_name}' environment config",
            emoji="🗑",
        )
        def delete_env_parameter(env_name: str | None):
            """
            .. note::

                - ssm_client is per environment bsm
                - s3_client is always devops bsm
            """
            if env_name is not None:
                env = self.config.get_env(env_name=env_name)
                result = self.config.delete_env_parameter(
                    ssm_client=self.bsm_enum.get_env_bsm(env_name=env_name).ssm_client,
                    env_name=env_name,
                    s3_client=self.bsm_enum.bsm_devops.s3_client,
                    include_s3=True,
                    s3dir_config=env.s3dir_config_artifacts,
                )
            else:
                result = self.config.delete_env_parameter(
                    ssm_client=self.bsm_enum.bsm_devops.ssm_client,
                    s3_client=self.bsm_enum.bsm_devops.s3_client,
                    include_s3=True,
                    s3dir_config=self.config.dev.s3dir_config_artifacts,
                )

            name = result.parameter_name
            url = self.aws_console.ssm.get_parameter(name_or_arn=name)
            logger.info(f"Deleted ssm parameter {name = }, {url = }")

            if result.s3dir_config is not None:
                url = result.s3dir_config.console_url
                logger.info(f"Deleted S3 config artifacts, {url = }")

        delete_env_parameter(env_name=None)
        delete_env_parameter(env_name=EnvNameEnum.dev.value)
        delete_env_parameter(env_name=EnvNameEnum.tst.value)
        delete_env_parameter(env_name=EnvNameEnum.prd.value)
