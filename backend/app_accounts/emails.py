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

from core.mail import mail_language

from .models import User
from .tokens import ACTIVATION, make_link_token

logger = logging.getLogger(__name__)

RESET_PATH = '/passwort-zuruecksetzen'
ACTIVATION_PATH = '/konto-aktivieren'
SUBJECTS = {
    'password_reset': {'de': 'Neues Passwort für SnipAtlas', 'en': 'New password for SnipAtlas'},
    'activation': {
        'de': 'Bestätige dein Konto bei SnipAtlas',
        'en': 'Confirm your SnipAtlas account',
    },
    'existing_account': {'de': 'Dein Konto bei SnipAtlas', 'en': 'Your SnipAtlas account'},
}


def frontend_link(path: str, user: User, token: str) -> str:
    """Return the frontend link with the encoded user id and the token."""
    query = urlencode({'uid': urlsafe_base64_encode(force_bytes(user.pk)), 'token': token})
    return f'{settings.FRONTEND_URL}{path}?{query}'


def reset_link(user: User) -> str:
    """Return the frontend link with uid and token for a password reset."""
    return frontend_link(RESET_PATH, user, default_token_generator.make_token(user))


def send_reset_mail(user: User) -> None:
    """Send the password reset mail."""
    _send('password_reset', user.email, reset_link(user))


def send_activation_mail(user: User) -> None:
    """Send the mail with the link that confirms a new account."""
    link = frontend_link(ACTIVATION_PATH, user, make_link_token(user, ACTIVATION))
    _send('activation', user.email, link)


def send_existing_account_mail(user: User) -> None:
    """Tell the owner of a confirmed address that they already have an account."""
    _send('existing_account', user.email, settings.FRONTEND_URL)


def _send(template: str, to: str, link: str) -> None:
    """Send a plain text mail in the request language and log errors instead of raising."""
    language = mail_language()
    body = render_to_string(f'app_accounts/emails/{language}/{template}.txt', {'link': link})
    try:
        EmailMessage(SUBJECTS[template][language], body, to=[to]).send()
    except SMTPException, OSError:
        logger.exception('Mail "%s" failed', template)
