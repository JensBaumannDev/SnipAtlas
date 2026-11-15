import threading
from smtplib import SMTPException

import environ
import pytest
from django.core import mail
from django.test import override_settings
from django.utils import translation
from pytest_django import Settings

from core.mail import mail_language, mailer_config, send_in_background

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


@pytest.mark.parametrize(('active', 'expected'), [('de', 'de'), ('en', 'en'), ('en-us', 'en')])
def test_mail_language_follows_active_language(active: str, expected: str) -> None:
    with translation.override(active):
        assert mail_language() == expected


@pytest.mark.parametrize('code', ['en', 'EN', 'en-GB'])
def test_mail_language_accepts_given_english_code(code: str) -> None:
    assert mail_language(code) == 'en'


@pytest.mark.parametrize('code', ['de', 'fr', 'auto', '', 'xx'])
def test_mail_language_falls_back_to_german(code: str) -> None:
    with translation.override('en'):
        assert mail_language(code) == 'de'


def test_mail_language_without_active_language_is_german() -> None:
    with translation.override(None):
        assert mail_language() == 'de'


# Sending in the background

BACKGROUND_WAIT = 5


def message() -> mail.EmailMessage:
    return mail.EmailMessage('Subject', 'Body', to=['to@example.com'])


def blocking_send(monkeypatch: pytest.MonkeyPatch) -> threading.Event:
    release = threading.Event()

    def send(self: mail.EmailMessage, fail_silently: bool = False) -> int:
        assert release.wait(BACKGROUND_WAIT)
        mail.outbox.append(self)
        return 1

    monkeypatch.setattr(mail.EmailMessage, 'send', send)
    return release


def test_background_mail_returns_before_it_is_sent(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.MAIL_IN_BACKGROUND = True
    release = blocking_send(monkeypatch)
    thread = send_in_background(message(), 'test')
    assert thread is not None and thread.is_alive()
    assert mail.outbox == []
    release.set()
    thread.join(BACKGROUND_WAIT)
    assert len(mail.outbox) == 1


def test_background_mail_reaches_the_outbox(settings: Settings) -> None:
    settings.MAIL_IN_BACKGROUND = True
    thread = send_in_background(message(), 'test')
    assert thread is not None
    thread.join(BACKGROUND_WAIT)
    assert [sent.to for sent in mail.outbox] == [['to@example.com']]


def test_server_waits_for_background_mail_on_shutdown(settings: Settings) -> None:
    settings.MAIL_IN_BACKGROUND = True
    thread = send_in_background(message(), 'test')
    assert thread is not None and not thread.daemon
    thread.join(BACKGROUND_WAIT)


def test_mail_is_sent_at_once_when_background_is_off(settings: Settings) -> None:
    settings.MAIL_IN_BACKGROUND = False
    assert send_in_background(message(), 'test') is None
    assert len(mail.outbox) == 1


@pytest.mark.parametrize('background', [True, False])
@pytest.mark.parametrize('error', [SMTPException, OSError])
def test_failing_mail_is_logged_not_raised(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    background: bool,
    error: type[Exception],
) -> None:
    settings.MAIL_IN_BACKGROUND = background

    def fail(self: mail.EmailMessage, fail_silently: bool = False) -> int:
        raise error

    monkeypatch.setattr(mail.EmailMessage, 'send', fail)
    thread = send_in_background(message(), 'test')
    if thread:
        thread.join(BACKGROUND_WAIT)
    assert 'Mail "test" failed' in caplog.text


def test_background_is_on_in_project_settings() -> None:
    from core import settings as project_settings

    assert project_settings.MAIL_IN_BACKGROUND is True
