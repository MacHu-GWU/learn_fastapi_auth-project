# -*- coding: utf-8 -*-

"""
Multi-account AWS boto session management for cloud-native applications.

This module provides unified boto session management across multiple AWS accounts and environments,
enabling seamless authentication, cross-account resource access, and environment-aware credential
handling while maintaining security boundaries and preventing operational errors.

.. seealso::

    :ref:`Boto-Session-For-Multi-AWS-Account`
"""

import os
import dataclasses
from functools import cached_property

from boto_session_manager import BotoSesManager
from aws_console_url.api import AWSConsole

from which_bsm.api import BaseBotoSesEnum

from .runtime import runtime
from .env import EnvNameEnum, detect_current_env


@dataclasses.dataclass
class BotoSesEnum(BaseBotoSesEnum):
    """
    Environment-aware boto session enumeration for multi-account AWS access.

    Provides centralized session management with automatic environment detection, cross-account
    credential handling, and integrated AWS console URL generation for seamless multi-environment
    operations while enforcing security boundaries and preventing accidental cross-environment access.
    """

    @cached_property
    def bsm_dev(self):
        """
        BotoSesManager for dev environment.
        """
        return self.get_env_bsm(env_name=EnvNameEnum.dev.value)

    @cached_property
    def bsm_tst(self):
        """
        BotoSesManager for tst environment.
        """
        return self.get_env_bsm(env_name=EnvNameEnum.tst.value)

    @cached_property
    def bsm_prd(self):
        """
        BotoSesManager for prd environment.
        """
        return self.get_env_bsm(env_name=EnvNameEnum.prd.value)

    @cached_property
    def workload_bsm_list(self):
        """
        List of BotoSesManager for all workload environments.
        """
        return [
            self.bsm_dev,
            self.bsm_tst,
            self.bsm_prd,
        ]

    def print_who_am_i(self):  # pragma: no cover
        """
        Print who am I for all boto sessions.
        """
        masked = not runtime.is_local_runtime_group
        for name, bsm in [
            ("bsm_devops", self.bsm_devops),
            ("bsm_dev", self.bsm_dev),
            ("bsm_tst", self.bsm_tst),
            ("bsm_prd", self.bsm_prd),
        ]:
            print(f"--- {name} ---")
            bsm.print_who_am_i(masked=masked)

    @cached_property
    def bsm(self) -> "BotoSesManager":
        """
        BotoSesManager for the current environment.
        """
        from s3pathlib import context

        if runtime.is_vercel:  # pragma: no cover
            bsm = BotoSesManager(region_name=os.environ["AWS_DEFAULT_REGION"])
        else:
            current_env = detect_current_env()
            bsm = self.get_env_bsm(env_name=current_env)
        context.attach_boto_session(boto_ses=bsm.boto_ses)
        return bsm

    @cached_property
    def aws_console(self) -> "AWSConsole":  # pragma: no cover
        """
        AWSConsole for the current environment.
        """
        return AWSConsole.from_bsm(self.bsm)

    @cached_property
    def aws_console_devops(self) -> "AWSConsole":  # pragma: no cover
        """
        AWSConsole for the devops environment.
        """
        return AWSConsole.from_bsm(self.bsm)

    @classmethod
    def new(cls):
        """
        Create a new BotoSesEnum instance with predefined environment mappings.
        """
        return cls(
            env_to_aws_profile_mapper={
                EnvNameEnum.devops.value: "esc_app_devops_us_east_1",
                EnvNameEnum.dev.value: "esc_app_dev_us_east_1",
                EnvNameEnum.tst.value: "esc_app_test_us_east_1",
                EnvNameEnum.prd.value: "esc_app_prod_us_east_1",
            },
            env_to_aws_region_mapper={
                EnvNameEnum.devops.value: "us-east-1",
                EnvNameEnum.dev.value: "us-east-1",
                EnvNameEnum.tst.value: "us-east-1",
                EnvNameEnum.prd.value: "us-east-1",
            },
            default_app_env_name=EnvNameEnum.dev.value,
            devops_env_name=EnvNameEnum.devops.value,
            workload_role_name_prefix_in_ci="learn_fastapi_auth_",
            workload_role_name_suffix_in_ci="_deployer",
            is_local_runtime_group=runtime.is_local_runtime_group,
            is_ci_runtime_group=runtime.is_ci_runtime_group,
            is_local=runtime.is_local,
            is_cloud9=runtime.is_aws_cloud9,
            is_ec2=runtime.is_aws_ec2,
            is_lambda=runtime.is_aws_lambda,
            is_batch=runtime.is_aws_batch,
            is_ecs=runtime.is_aws_ecs,
            is_glue=runtime.is_aws_glue,
        )