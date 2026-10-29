"""App configuration for the feedback app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppFeedbackConfig(AppConfig):
    """Configuration of the feedback app."""

    name = 'app_feedback'
    verbose_name = _('Requests')
