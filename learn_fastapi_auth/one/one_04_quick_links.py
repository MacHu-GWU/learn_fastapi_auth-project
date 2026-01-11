# -*- coding: utf-8 -*-

"""
Quick links generation mixin for documentation and resource navigation.

This module provides automatic generation of structured quick links for AWS resources,
GitHub repositories, local file paths, and S3 storage locations, creating reStructuredText
tables for easy navigation and resource discovery in project documentation.
"""

import typing as T

from aws_console_url.api import AWSConsole

from ..lazy_imports import rstobj

from ..paths import path_enum
from ..env import EnvNameEnum

if T.TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path
    from s3pathlib import S3Path

    from .one_00_main import One


def encode_url(url: str, title: str | None = None) -> "rstobj.URL":
    """Create reStructuredText URL object with optional custom title."""
    if title:
        return rstobj.URL(title=title, link=url)
    else:
        return rstobj.URL(title=url, link=url)


class OneQuickLinksMixin:  # pragma: no cover
    """
    Mixin providing automated quick links generation for project resources.
    """
    def get_path_quick_link_row(
        self: "One",
        name: str,
        path: "S3Path",
    ) -> list:
        """
        Generate table row for local file system path quick link.
        """
        relpath = path.relative_to(path_enum.dir_project_root)
        return [
            "🗂Local Path",
            name,
            encode_url(
                url=f"file://{path}",
                title=f"$dir_project_root/{str(relpath)}",
            ),
        ]

    def get_github_quick_link_row(
        self: "One",
        name: str,
        path: "Path",
    ) -> list:
        """
        Generate table row for GitHub repository quick link.
        """
        relpath = path.relative_to(path_enum.dir_project_root)
        p = "/".join(relpath.parts)
        main_branch = "main"
        if path.is_file():
            url = f"{self.pywf.github_repo_url}/blob/{main_branch}/{p}"
        else:
            url = f"{self.pywf.github_repo_url}/tree/{main_branch}/{p}"
        return [
            "🐙GitHub",
            name,
            encode_url(
                url=url,
            ),
        ]

    def get_s3path_quick_link_row(
        self: "One",
        name: str,
        s3path: "S3Path",
    ) -> list:
        """
        Generate table row for S3 bucket quick link.
        """
        return [
            "🪣AWS S3",
            name,
            encode_url(
                url=s3path.console_url,
                title=s3path.uri,
            ),
        ]

    def generate_quick_links_for_project(self: "One") -> str:
        """
        Generate reStructuredText table of project-wide resource quick links.
        """
        env = self.config.devops
        bsm = self.bsm_devops
        aws_console = AWSConsole.from_bsm(bsm=bsm)

        rows = list()
        columns = "Group,Resource Name,URL".split(",")
        rows.append(columns)

        for name, path in [
            ("GitHub Repo", path_enum.dir_project_root),
            ("Python Library", path_enum.dir_python_lib),
            ("pyproject.toml", path_enum.path_pyproject_toml),
            ("Project config.json", path_enum.path_config_json),
            ("Project secret-config.json", path_enum.path_secret_config_json),
            ("Unit Test Dir", path_enum.dir_unit_test),
            ("Integration Test Dir", path_enum.dir_int_test),
            ("Documents Dir", path_enum.dir_docs_source),
        ]:
            rows.append(self.get_github_quick_link_row(name, path))

        for name, path in [
            ("Project Root", path_enum.dir_project_root),
            ("Python Library", path_enum.dir_python_lib),
            ("pyproject.toml", path_enum.path_pyproject_toml),
            ("dir_venv", path_enum.dir_venv),
            ("virtualenv Python", path_enum.path_venv_bin_python),
            ("Project config.json", path_enum.path_config_json),
            ("Project secret-config.json", path_enum.path_secret_config_json),
            ("Unit Test Dir", path_enum.dir_unit_test),
            ("Integration Test Dir", path_enum.dir_int_test),
            ("Documents Dir", path_enum.dir_docs_source),
        ]:
            rows.append(self.get_path_quick_link_row(name, path))

        for name, s3path in [
            ("s3dir_artifacts", env.s3dir_artifacts),
            ("s3dir_config", env.s3dir_config_artifacts),
        ]:
            rows.append(self.get_s3path_quick_link_row(name, s3path))

        rows.extend(
            [
                [
                    "⚙️AWS Parameter Store",
                    self.config.parameter_name,
                    encode_url(
                        aws_console.ssm.get_parameter(self.config.parameter_name)
                    ),
                ],
            ]
        )

        ltable = rstobj.directives.ListTable(
            data=rows,
            title=f"Project",
            header=True,
        )
        return ltable.render()

    def generate_quick_links_for_env(self: "One", env_name: str) -> str:
        """
        Generate reStructuredText table of environment-specific resource quick links.
        """
        rows = list()
        columns = "Group,Resource Name,URL".split(",")
        rows.append(columns)

        env = self.config.get_env(env_name=env_name)
        bsm = self.bsm_enum.get_env_bsm(env_name=env_name)
        aws_console = AWSConsole.from_bsm(bsm=bsm)

        for name, s3path in [
            ("s3dir_data", env.s3dir_data),
        ]:
            rows.append(self.get_s3path_quick_link_row(name, s3path))

        rows.extend(
            [
                [
                    "⚙️AWS Parameter Store",
                    env.parameter_name,
                    encode_url(aws_console.ssm.get_parameter(env.parameter_name)),
                ],
            ]
        )
        ltable = rstobj.directives.ListTable(
            data=rows,
            title=f"Env = {env_name}",
            header=True,
        )

        return ltable.render()

    def generate_quick_links(self: "One"):
        """
        Generate and write all quick links documentation files.
        """
        basename = f"project-quick-links.rst"
        path = path_enum.dir_quick_links.joinpath(basename)
        content = self.generate_quick_links_for_project()
        path.write_text(content, encoding="utf-8")

        for env in EnvNameEnum:
            if env != EnvNameEnum.devops:
                content = self.generate_quick_links_for_env(env_name=env.value)
                basename = f"{env.value}-quick-links.rst"
                path = path_enum.dir_quick_links.joinpath(basename)
                path.write_text(content, encoding="utf-8")
                # break
