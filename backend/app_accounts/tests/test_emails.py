import threading

import pytest
from django.core import mail
from django.urls import reverse
from pytest_django import Settings
from rest_framework.test import APIClient

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
GERMAN = ['de', 'de-DE,de;q=0.9', 'fr', 'fr-FR,fr;q=0.9', '', 'xx-invalid']
ENGLISH = ['en', 'en-US,en;q=0.9', 'EN', 'fr;q=0.5,en;q=0.9']

SUBJECTS = {
    'reset': ('Neues Passwort für SnipAtlas', 'New password for SnipAtlas'),
    'activation': ('Bestätige dein Konto bei SnipAtlas', 'Confirm your SnipAtlas account'),
    'existing': ('Dein Konto bei SnipAtlas', 'Your SnipAtlas account'),
}
PHRASES = {
    'reset': ('Der Link gilt eine Stunde', 'The link is valid for one hour'),
    'activation': ('Der Link gilt 24 Stunden', 'The link is valid for 24 hours'),
    'existing': ('Du hast aber schon ein Konto', 'you already have an account'),
}


def trigger(api_client: APIClient, kind: str, language: str) -> None:
    headers = {'HTTP_ACCEPT_LANGUAGE': language} if language else {}
    if kind == 'reset':
        data, url = {'email': 'ada@example.com'}, reverse('auth-password-reset')
    else:
        email = 'grace@example.com' if kind == 'activation' else 'ada@example.com'
        data, url = {'email': email, 'password': PASSWORD}, reverse('auth-register')
    response = api_client.post(url, data, format='json', **headers)
    assert response.status_code == 204


@pytest.mark.parametrize('kind', SUBJECTS)
@pytest.mark.parametrize('language', GERMAN)
def test_mail_is_german_by_default(
    api_client: APIClient, user: User, kind: str, language: str
) -> None:
    trigger(api_client, kind, language)
    message = mail.outbox[0]
    assert message.subject == SUBJECTS[kind][0]
    assert PHRASES[kind][0] in message.body
    assert PHRASES[kind][1] not in message.body


@pytest.mark.parametrize('kind', SUBJECTS)
@pytest.mark.parametrize('language', ENGLISH)
def test_mail_follows_english_request_language(
    api_client: APIClient, user: User, kind: str, language: str
) -> None:
    trigger(api_client, kind, language)
    message = mail.outbox[0]
    assert message.subject == SUBJECTS[kind][1]
    assert PHRASES[kind][1] in message.body
    assert PHRASES[kind][0] not in message.body


@pytest.mark.parametrize('kind', SUBJECTS)
@pytest.mark.parametrize('language', ['de', 'en'])
def test_mail_in_both_languages_keeps_link_and_sender(
    api_client: APIClient, user: User, kind: str, language: str
) -> None:
    trigger(api_client, kind, language)
    message = mail.outbox[0]
    assert 'http://localhost:4200' in message.body
    assert message.from_email == 'noreply@snipatlas.jensbaumann.com'
    assert message.content_subtype == 'plain'
    assert '<' not in message.body


def test_mail_language_follows_request_not_saved_setting(api_client: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(language='de')
    trigger(api_client, 'reset', 'en')
    assert mail.outbox[0].subject == SUBJECTS['reset'][1]


@pytest.mark.parametrize('kind', SUBJECTS)
def test_response_does_not_wait_for_the_mail(
    api_client: APIClient,
    user: User,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    settings.MAIL_IN_BACKGROUND = True
    release = threading.Event()

    def send(self: mail.EmailMessage, fail_silently: bool = False) -> int:
        assert release.wait(5)
        mail.outbox.append(self)
        return 1

    monkeypatch.setattr(mail.EmailMessage, 'send', send)
    trigger(api_client, kind, 'de')
    assert mail.outbox == []
    release.set()
    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            thread.join(5)
    assert mail.outbox[0].subject == SUBJECTS[kind][0]
