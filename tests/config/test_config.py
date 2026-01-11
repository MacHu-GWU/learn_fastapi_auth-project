# -*- coding: utf-8 -*-

from learn_fastapi_auth.one.api import one


def test():
    config = one.config

    env = config.env

    _ = env.db_host
    _ = env.db_user
    _ = env.db_pass
    _ = env.db_name
    _ = env.secret_key
    _ = env.smtp_host
    _ = env.smtp_port
    _ = env.smtp_tls
    _ = env.smtp_user
    _ = env.smtp_password
    _ = env.smtp_from
    _ = env.smtp_from_name
    _ = env.frontend_url
    _ = env.verification_token_lifetime
    _ = env.reset_password_token_lifetime
    _ = env.access_token_lifetime
    _ = env.refresh_token_lifetime
    _ = env.remember_me_refresh_token_lifetime
    _ = env.refresh_token_cookie_name
    _ = env.refresh_token_cookie_secure
    _ = env.refresh_token_cookie_samesite
    _ = env.rate_limit_login
    _ = env.rate_limit_register
    _ = env.rate_limit_forgot_password
    _ = env.rate_limit_default
    _ = env.csrf_cookie_name
    _ = env.csrf_cookie_secure
    _ = env.csrf_cookie_samesite
    _ = env.firebase_enabled

    _ = env.async_db_url
    _ = env.final_front_end_url
    _ = env.firebase_cert_parameter_name
    _ = env.get_firebase_cert(bsm=one.bsm)


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.config",
        is_folder=True,
        preview=False,
    )
