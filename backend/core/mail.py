"""Mail backend configuration read from environment variables."""

import environ

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
