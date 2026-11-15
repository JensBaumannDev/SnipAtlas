"""Mails sent to users of the accounts app."""

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.mail import mail_language, send_in_background

from .models import User
from .tokens import ACTIVATION, EMAIL_CHANGE, make_link_token

RESET_PATH = '/passwort-zuruecksetzen'
ACTIVATION_PATH = '/konto-aktivieren'
EMAIL_CHANGE_PATH = '/email-bestaetigen'
SUBJECTS = {
    'password_reset': {'de': 'Neues Passwort für SnipAtlas', 'en': 'New password for SnipAtlas'},
    'activation': {
        'de': 'Bestätige dein Konto bei SnipAtlas',
        'en': 'Confirm your SnipAtlas account',
    },
    'existing_account': {'de': 'Dein Konto bei SnipAtlas', 'en': 'Your SnipAtlas account'},
    'email_change': {
        'de': 'Bestätige deine neue E-Mail-Adresse',
        'en': 'Confirm your new email address',
    },
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


def send_email_change_mail(user: User) -> None:
    """Send the link that confirms the pending address to that address."""
    link = frontend_link(EMAIL_CHANGE_PATH, user, make_link_token(user, EMAIL_CHANGE))
    _send('email_change', user.pending_email, link)


def _send(template: str, to: str, link: str) -> None:
    """Send a plain text mail in the request language in the background."""
    language = mail_language()
    body = render_to_string(f'app_accounts/emails/{language}/{template}.txt', {'link': link})
    send_in_background(EmailMessage(SUBJECTS[template][language], body, to=[to]), template)
