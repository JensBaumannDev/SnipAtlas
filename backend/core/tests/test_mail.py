import environ
import pytest
from django.core import mail
from django.test import override_settings

from core.mail import mailer_config

SMTP = 'django.core.mail.backends.smtp.EmailBackend'
CONSOLE = 'django.core.mail.backends.console.EmailBackend'


@pytest.fixture
def no_mail_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ('EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS'):
        monkeypatch.delenv(name, raising=False)


def test_default_backend_is_console_without_smtp_options(no_mail_env: None) -> None:
    assert mailer_config(environ.Env()) == {'BACKEND': CONSOLE}


def test_default_config_sends_mail_without_error(no_mail_env: None) -> None:
    with override_settings(MAILERS={'default': mailer_config(environ.Env())}):
        sent = mail.send_mail('Subject', 'Body', 'from@example.com', ['to@example.com'])
    assert sent == 1


def test_smtp_backend_gets_options_from_env(
    no_mail_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('EMAIL_BACKEND', SMTP)
    monkeypatch.setenv('EMAIL_HOST', 'smtp.resend.com')
    monkeypatch.setenv('EMAIL_HOST_USER', 'resend')
    monkeypatch.setenv('EMAIL_HOST_PASSWORD', 'secret')
    assert mailer_config(environ.Env()) == {
        'BACKEND': SMTP,
        'OPTIONS': {
            'host': 'smtp.resend.com',
            'port': 587,
            'username': 'resend',
            'password': 'secret',
            'use_tls': True,
        },
    }
