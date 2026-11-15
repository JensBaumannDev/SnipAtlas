from smtplib import SMTPException
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core import mail
from django.core.mail import EmailMessage
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User
from app_accounts.tokens import ACTIVATION, check_link_token

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-activate-resend')


@pytest.fixture
def new_user() -> User:
    return User.objects.create_user('grace@example.com', PASSWORD, email_confirmed=False)


def resend(client: APIClient, email: object = 'grace@example.com', **extra: str) -> Response:
    return client.post(URL, {'email': email}, format='json', **extra)


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def token_in(body: str) -> str:
    link = next(word for word in body.split() if 'konto-aktivieren' in word)
    return parse_qs(urlsplit(link).query)['token'][0]


# Mail
def test_resend_sends_activation_mail(api_client: APIClient, new_user: User) -> None:
    response = resend(api_client)
    assert (response.status_code, response.content) == (204, b'')
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ['grace@example.com']
    assert message.subject == 'Bestätige dein Konto bei SnipAtlas'
    assert check_link_token(new_user, token_in(message.body), ACTIVATION)


def test_resend_uses_request_language(api_client: APIClient, new_user: User) -> None:
    resend(api_client, HTTP_ACCEPT_LANGUAGE='en')
    assert mail.outbox[0].subject == 'Confirm your SnipAtlas account'


def test_resend_finds_email_in_other_case(api_client: APIClient, new_user: User) -> None:
    resend(api_client, ' GRACE@Example.com ')
    assert mail.outbox[0].to == ['grace@example.com']


def test_resend_changes_nothing(api_client: APIClient, new_user: User) -> None:
    resend(api_client)
    new_user.refresh_from_db()
    assert not new_user.email_confirmed
    assert new_user.check_password(PASSWORD)


def test_resend_does_not_log_in(api_client: APIClient, new_user: User) -> None:
    resend(api_client)
    assert api_client.get(reverse('auth-me')).status_code == 204


def test_resend_ignores_other_fields(api_client: APIClient, new_user: User) -> None:
    data = {'email': 'grace@example.com', 'to': 'evil@example.com', 'user': 1}
    api_client.post(URL, data, format='json')
    assert [message.to for message in mail.outbox] == [['grace@example.com']]


# Same answer, no mail
def test_resend_for_confirmed_user_sends_no_mail(api_client: APIClient, user: User) -> None:
    response = resend(api_client, 'ada@example.com')
    assert (response.status_code, response.content) == (204, b'')
    assert mail.outbox == []


def test_resend_for_unknown_email_sends_no_mail(api_client: APIClient, new_user: User) -> None:
    response = resend(api_client, 'unknown@example.com')
    assert (response.status_code, response.content) == (204, b'')
    assert mail.outbox == []
    assert not User.objects.filter(email='unknown@example.com').exists()


def test_resend_for_deactivated_user_sends_no_mail(api_client: APIClient, new_user: User) -> None:
    User.objects.filter(pk=new_user.pk).update(is_active=False)
    assert resend(api_client).status_code == 204
    assert mail.outbox == []


def test_resend_with_unicode_lookalike_sends_no_mail(api_client: APIClient, db: None) -> None:
    User.objects.create_user('tim@example.com', PASSWORD, email_confirmed=False)
    for lookalike in ['tım@example.com', 'TİM@example.com']:
        resend(api_client, lookalike)
    assert mail.outbox == []


def test_resend_with_failing_mail_answers_the_same(
    api_client: APIClient, new_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: EmailMessage, fail_silently: bool = False) -> int:
        raise SMTPException

    monkeypatch.setattr(EmailMessage, 'send', fail)
    response = resend(api_client)
    assert (response.status_code, response.content) == (204, b'')


# Invalid fields
@pytest.mark.parametrize(
    ('email', 'code'),
    [
        ('', 'blank'),
        (None, 'null'),
        ('grace', 'invalid'),
        (['grace@example.com'], 'invalid'),
        ('grace@example.com\x00', 'null_characters_not_allowed'),
        (f'{"a" * 243}@example.com', 'max_length'),
    ],
)
def test_resend_with_invalid_email_is_rejected(
    api_client: APIClient, new_user: User, email: object, code: str
) -> None:
    assert code in field_errors(resend(api_client, email))['email']
    assert mail.outbox == []


def test_resend_without_email_is_rejected(api_client: APIClient) -> None:
    assert field_errors(api_client.post(URL, {}, format='json')) == {'email': ['required']}


def test_resend_with_list_body_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, ['email'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}


# Security
def test_resend_without_csrf_token_is_rejected(csrf_client: APIClient, new_user: User) -> None:
    response = resend(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert mail.outbox == []


def test_resend_with_csrf_token_is_allowed(csrf_client: APIClient, new_user: User) -> None:
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    assert resend(csrf_client, HTTP_X_CSRFTOKEN=CSRF_TOKEN).status_code == 204


def test_resend_is_throttled_after_three_attempts(api_client: APIClient, new_user: User) -> None:
    for email in ['unknown@example.com', 'grace', 'grace@example.com']:
        resend(api_client, email)
    response = resend(api_client)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert len(mail.outbox) == 1


def test_resend_shares_limit_with_password_reset(api_client: APIClient, new_user: User) -> None:
    for _ in range(3):
        api_client.post(reverse('auth-password-reset'), {'email': 'x@example.com'}, format='json')
    assert resend(api_client).status_code == 429
    assert mail.outbox == []


def test_resend_limit_is_separate_from_login(api_client: APIClient, new_user: User) -> None:
    login = {'email': 'grace@example.com', 'password': 'Falsches-Passwort-1'}
    for _ in range(5):
        api_client.post(reverse('auth-login'), login, format='json')
    assert resend(api_client).status_code == 204


def test_resend_throttles_per_ip(api_client: APIClient, new_user: User) -> None:
    for _ in range(3):
        resend(api_client, 'unknown@example.com')
    assert resend(api_client, REMOTE_ADDR='10.0.0.2').status_code == 204


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_resend_rejects_other_methods(api_client: APIClient, new_user: User, method: str) -> None:
    response = getattr(api_client, method)(URL, {'email': 'grace@example.com'}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert mail.outbox == []
