"""Mails sent to users of the accounts app."""

import logging
from smtplib import SMTPException
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User
from .tokens import ACTIVATION, make_link_token

logger = logging.getLogger(__name__)

RESET_SUBJECT = 'Neues Passwort für SnipAtlas'
RESET_PATH = '/passwort-zuruecksetzen'
ACTIVATION_SUBJECT = 'Bestätige dein Konto bei SnipAtlas'
ACTIVATION_PATH = '/konto-aktivieren'
EXISTING_ACCOUNT_SUBJECT = 'Dein Konto bei SnipAtlas'


def frontend_link(path: str, user: User, token: str) -> str:
    """Return the frontend link with the encoded user id and the token."""
    query = urlencode({'uid': urlsafe_base64_encode(force_bytes(user.pk)), 'token': token})
    return f'{settings.FRONTEND_URL}{path}?{query}'


def reset_link(user: User) -> str:
    """Return the frontend link with uid and token for a password reset."""
    return frontend_link(RESET_PATH, user, default_token_generator.make_token(user))


def send_reset_mail(user: User) -> None:
    """Send the password reset mail."""
    _send(RESET_SUBJECT, 'password_reset', user.email, reset_link(user))


def send_activation_mail(user: User) -> None:
    """Send the mail with the link that confirms a new account."""
    link = frontend_link(ACTIVATION_PATH, user, make_link_token(user, ACTIVATION))
    _send(ACTIVATION_SUBJECT, 'activation', user.email, link)


def send_existing_account_mail(user: User) -> None:
    """Tell the owner of a confirmed address that they already have an account."""
    _send(EXISTING_ACCOUNT_SUBJECT, 'existing_account', user.email, settings.FRONTEND_URL)


def _send(subject: str, template: str, to: str, link: str) -> None:
    """Send a plain text mail and log errors instead of raising them."""
    body = render_to_string(f'app_accounts/emails/{template}.txt', {'link': link})
    try:
        EmailMessage(subject, body, to=[to]).send()
    except SMTPException, OSError:
        logger.exception('Mail "%s" failed', subject)
