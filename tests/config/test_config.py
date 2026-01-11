# -*- coding: utf-8 -*-

from learn_fastapi_auth.one.api import one


def test():
    config = one.config

    env = config.env

    _ = env.s3dir_source
    _ = env.s3dir_target



if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.config",
        is_folder=True,
        preview=False,
    )
