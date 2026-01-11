# -*- coding: utf-8 -*-

"""
Singleton Variable Access Subpackage

This subpackage provides a singleton variable access system using a lazy loading pattern.
The purpose is to enable safe imports without creating unnecessary dependencies between
different components of the application.

By implementing lazy loading, the 'one' subpackage ensures that resources are only
initialized when actually needed. For example, when accessing a boto3 session, the
system will not unnecessarily create a database connection, which is another
singleton object. This approach prevents circular dependencies and reduces
startup time by avoiding premature initialization of heavy resources.
"""
