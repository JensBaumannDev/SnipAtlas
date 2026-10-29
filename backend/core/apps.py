"""App configuration that replaces the default admin site."""

from django.contrib.admin.apps import AdminConfig


class SnipAtlasAdminConfig(AdminConfig):
    """Admin configuration that uses the SnipAtlas admin site."""

    default_site = 'core.admin.SnipAtlasAdminSite'
