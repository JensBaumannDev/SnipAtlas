"""App configuration for the accounts app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppAccountsConfig(AppConfig):
    """Configuration of the accounts app."""

    name = 'app_accounts'
    verbose_name = _('Accounts')
