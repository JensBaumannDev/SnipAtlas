"""Settings helpers for running the project behind the server proxy."""

import re

from django.core.exceptions import ImproperlyConfigured

ADMIN_PATH_PATTERN = re.compile(r'[a-z0-9][a-z0-9-]*/')
RESERVED_PATHS = ('api/', 'static/')


def admin_path(value: str) -> str:
    """Return the admin URL prefix, one lowercase path segment that ends with a slash."""
    if not ADMIN_PATH_PATTERN.fullmatch(value) or value in RESERVED_PATHS:
        raise ImproperlyConfigured(f'ADMIN_PATH must look like "admin/", got "{value}".')
    return value
