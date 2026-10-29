"""App configuration for the content app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppContentConfig(AppConfig):
    """Configuration of the content app."""

    name = 'app_content'
    verbose_name = _('Content')
