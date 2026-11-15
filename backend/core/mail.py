"""Mail backend configuration, sending in the background and the language of mails."""

import logging
from smtplib import SMTPException
from threading import Thread

import environ
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import translation

logger = logging.getLogger(__name__)

MAIL_LANGUAGES = ('de', 'en')
CONSOLE_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SMTP_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


def mailer_config(env: environ.Env) -> dict:
    """Return the default mailer, with SMTP options only for the SMTP backend."""
    backend = env('EMAIL_BACKEND', default=CONSOLE_BACKEND)
    if backend != SMTP_BACKEND:
        return {'BACKEND': backend}
    return {'BACKEND': backend, 'OPTIONS': _smtp_options(env)}


def _smtp_options(env: environ.Env) -> dict:
    """Return the SMTP connection options."""
    return {
        'host': env('EMAIL_HOST', default='localhost'),
        'port': env.int('EMAIL_PORT', default=587),
        'username': env('EMAIL_HOST_USER', default=''),
        'password': env('EMAIL_HOST_PASSWORD', default=''),
        'use_tls': env.bool('EMAIL_USE_TLS', default=True),
    }


def mail_language(code: str | None = None) -> str:
    """Return 'en' for an English language code, otherwise 'de'."""
    if code is None:
        code = translation.get_language() or ''
    language = code.lower().split('-')[0]
    return language if language in MAIL_LANGUAGES else MAIL_LANGUAGES[0]


def send_in_background(message: EmailMessage, name: str) -> Thread | None:
    """Send the mail in its own thread so the response time reveals nothing."""
    if not settings.MAIL_IN_BACKGROUND:
        _deliver(message, name)
        return None
    thread = Thread(target=_deliver, args=(message, name), name=f'mail-{name}')
    thread.start()
    return thread


def _deliver(message: EmailMessage, name: str) -> None:
    """Send the mail and log errors instead of raising."""
    try:
        message.send()
    except SMTPException, OSError:
        logger.exception('Mail "%s" failed', name)
