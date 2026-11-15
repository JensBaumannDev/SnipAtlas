"""Mail backend configuration and the language of mails."""

import environ
from django.utils import translation

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
